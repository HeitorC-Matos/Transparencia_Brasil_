# FastAPI — Guia de integração real com Streamlit

## Iniciar em dois terminais

Terminal 1: `uvicorn api.main:app --reload` (padrão `http://127.0.0.1:8000`).

Terminal 2: `streamlit run app.py`.

Swagger: http://127.0.0.1:8000/docs.

Se usar outro host/porta, configure `TP3_API_URL` no ambiente do **Streamlit**. O módulo `utils/api_client.py` é o único cliente HTTP usado pelas páginas. Não importa `api.main`, não lê CSVs na consulta HTTP e envia requests via `requests.get`/`requests.post` com timeout e tratamento de erros. Listagens são paginadas automaticamente até recuperar o total declarado pela API.

## Endpoints

| Método | Caminho | Quem o utiliza |
|---|---|---|
| GET | `/health` | Indicador de saúde e página API |
| GET | `/despesas` | Página Gastos, Estatísticas e página API (consultas por UF, função, origem, ano) |
| POST | `/despesas` | **Formulário Streamlit** na página API |
| GET | `/estatisticas` | Página Estatísticas e página API |
| GET | `/conteudo-web` | Página Conteúdo da Web; agrega BS e Selenium, se houver CSV Selenium válido |

### Consultar (GET)

```bash
curl "http://127.0.0.1:8000/despesas?sigla=SP&ano=2025&origem=amostra_academica"
curl "http://127.0.0.1:8000/estatisticas?origem=amostra_academica"
curl "http://127.0.0.1:8000/conteudo-web"
```

`GET /despesas` recebe `sigla=SP|GO|BA`, `ano`, `funcao`, `origem=amostra_academica|manual`, `limite=1..1000` e `deslocamento>=0`; devolve `total`, `limite`, `deslocamento` e uma lista `dados` com origem explícita e os campos fiscais. `/estatisticas` resume **uma origem por chamada**.

### Cadastrar (POST)

```bash
curl -X POST "http://127.0.0.1:8000/despesas" \
  -H "Content-Type: application/json" \
  -d '{"sigla":"GO","ano":2025,"funcao":"Educação","valor_despesa":1500.75,"populacao":7350000}'
```

O mesmo corpo pode ser enviado pelo formulário Streamlit na página **API FastAPI**. A FastAPI verifica tipos, UFs permitidas, funções, valores finitos positivos/não negativos e retorna HTTP 201, `id_registro`, `origem=manual` e data. Campos inválidos geram 422. Os dados são persistidos em `data/registros_manuais.csv` por gravação segura. O arquivo original `data/amostra_dados.csv` nunca é sobrescrito.

## Falhas e fallback

Se o processo FastAPI não estiver ligado, a interface identifica a falha. Algumas páginas permitem explorar a amostra local **com mensagem de modo offline**. O formulário não finge uma inserção offline, nem afirma sucesso sem receber retorno POST.

## Segurança

POST não tem autenticação, rate limit nem banco de dados transacional: **não publique a API na Internet** nessa configuração. Em hospedagens separadas, configurar comunicação segura, CORS caso seja necessário para frontends diretos (Streamlit usa HTTP servidor-a-servidor), persistência e controle de acesso.

---

## Rotas de processamento com modelo de linguagem local

As rotas de consulta, estatísticas e cadastro permanecem disponíveis. Foram acrescentadas:

- **`GET /ia/health`**: estado do modelo local (`arquivos_ausentes`, `nao_carregado`, `carregado` ou `erro_carregamento`). Não carrega os pesos.
- **`POST /processar_texto`**: recebe `texto` (obrigatório), `operacao` (`resumo` ou `explicacao`) e `max_novos_tokens` (32–512). Gera texto com Qwen3-4B-Instruct-2507 instalado na máquina, por meio de Transformers, PyTorch/CUDA e bitsandbytes, sem acesso ao Hugging Face Hub durante as requisições.

O corpo e a resposta estão descritos em [Guia de integração local](GUIA_LLM_LOCAL.md). Os contratos Pydantic são declarados nos argumentos `response_model` e agora abrangem todas as rotas. A validação também rejeita saídas vazias ou campos de tipo incorreto; o tratamento das exceções já distingue entradas inválidas, indisponibilidade, modelo ocupado, falhas internas e timeout, com códigos HTTP e identificadores de requisição. A API não baixa os pesos automaticamente. O primeiro uso realiza o carregamento a partir do disco, e somente uma geração por vez é permitida para preservar a memória da GPU.

**Comprovação:** 130 testes automatizados passaram na versão consolidada. O script HTTP `scripts/verificar_questao4.py` confirmou respostas 200, 422 e 404 com identificador de requisição, sem carregar o modelo. **A geração real do Qwen foi confirmada separadamente pelo usuário** em uma RTX 4060, tanto pela FastAPI quanto pelo Streamlit. Cenários excepcionais são exercitados nos testes com inferência simulada, sem provocar esgotamento real de VRAM.


## Contratos e validação dos dados de entrada e saída

O backend publica, em `/openapi.json` e `/docs`, os modelos de resposta de todas as rotas. `POST /processar_texto` usa `RequisicaoTexto` para entrada e `RespostaTexto` para saída; `GET /ia/health` usa `StatusModelo`. Esses modelos estão em `api/schemas/ia.py`.

O texto de entrada deve ter conteúdo legível e até 12.000 caracteres (a restrição adicional de 2.048 tokens é verificada no serviço local). A operação admite `resumo` ou `explicacao`. O máximo de novos tokens deve ser inteiro entre 32 e 512; campos desconhecidos e valores incorretos são rejeitados por HTTP 422 **antes** da inferência. A validação estrutural de saída exige texto não vazio, contagens positivas de tokens, tempo não negativo e execução local confirmada.

As rotas antigas possuem modelos definidos para as consultas de despesas, cadastro de despesas, estatísticas, catálogo Web e saúde; as consultas oficiais já têm contratos independentes. Os contratos gerais estão em `api/schemas/geral.py` e os modelos de despesas continuam em `api/main.py`.

Um retorno inválido gerado pelo backend é defeito interno e não uma entrada incorreta do usuário: o FastAPI/Pydantic não deve transformá-lo em HTTP 200. A API retorna erro de servidor, e testes independentes comprovam esse comportamento sem carregar os pesos do modelo. O tratamento e as mensagens de falhas mais especializadas serão desenvolvidos separadamente.

Verificação: `python -m pytest -q tests/test_contratos_resposta.py` e `http://127.0.0.1:8000/docs`.


## Tratamento padronizado de exceções

As rotas utilizam os manipuladores em `api/erros.py`. Respostas de erro são JSON e contêm `erro.codigo`, `erro.mensagem`, `erro.requisicao_id` e, quando necessário, `erro.detalhes`. O cabeçalho `X-Request-ID` acompanha os retornos para auxiliar o diagnóstico; o campo `detail` permanece por compatibilidade. Entradas inválidas geram 422 sem acionar o Qwen. Ocupação da GPU gera 429 com `Retry-After`, indisponibilidade ou falta de VRAM gera 503, falha interna gera 500 e estouro do limite cooperativo de geração gera 504. Erros estruturais na saída não são retornados como sucesso.

O Streamlit mostra mensagens compreensíveis para essas situações. O controle de concorrência continua limitado a uma geração por vez, e não é feita repetição automática de requisições que poderiam executar a mesma geração mais de uma vez. Para o diagnóstico HTTP sem GPU, utilize `python scripts/verificar_questao4.py` com a API em execução.
