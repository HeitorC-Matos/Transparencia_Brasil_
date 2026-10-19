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
