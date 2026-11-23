# Solução final com LLMs — automação de sumarização

## Caminho escolhido

O Transparência Brasil adotou a **Opção 2 — Automação de Sumarização de Textos com LLMs**. A solução utiliza o modelo **Qwen3-4B-Instruct-2507**, já instalado localmente na máquina de desenvolvimento. O objetivo não é substituir a análise numérica ou a conferência documental: é facilitar a leitura e a interpretação de informações sobre transparência pública, preservando as fontes utilizadas.

Optou-se pela sumarização porque o projeto já realiza coleta com Beautiful Soup e Selenium, organiza documentos em CSV/JSONL, mantém uma API FastAPI e dispõe de um assistente Qwen funcional. A memória conversacional e os agentes autônomos não são requisitos desta entrega.

## Fluxo completo da funcionalidade

**Textos institucionais:**

1. `coleta_web.py` obtém textos da ONU (ODS 16), do Tesouro Nacional (Siconfi) e da CGU, com Requests/Beautiful Soup. `coleta_selenium.py` obtém conteúdo governamental sobre transparência ativa. Esses processos já foram executados e seus resultados permanecem em `data/conteudo_web.csv` e `data/conteudo_selenium.csv`.
2. `services/documentos.py` lê **exclusivamente** esses arquivos locais, valida as colunas, elimina entradas sem conteúdo e monta identificadores determinísticos baseados na origem, URL e título. Nenhuma URL escolhida pelo usuário é solicitada à rede durante a sumarização. O catálogo atual contém quatro documentos institucionais.
3. `GET /ia/documentos` apresenta os documentos existentes, com título, método, URL e data da coleta.
4. `POST /ia/resumir_documento` recebe o identificador da fonte e o formato pretendido. O backend recupera o texto coletado, formula o prompt e consulta o Qwen, instalado em `models/qwen3-4b-instruct-2507/`.
5. Quando o documento não cabe em uma etapa, `services/sumarizacao.py` o divide em trechos, solicita sínteses intermediárias e em seguida consolida os resultados. **Não há corte silencioso**: documentos superiores ao limite de cinco trechos por solicitação recebem erro 422, acompanhado de orientação para fragmentá-los. Esse limite protege o uso local da GPU de 8 GB; não caracteriza suporte ilimitado a PDFs ou documentos extensos.
6. A FastAPI retorna a síntese, as URLs vinculadas, os parâmetros do prompt e as métricas de execução. O Streamlit apresenta o resultado na aba **Documentos coletados**, sem copiar e colar manualmente os textos.

**Dados fiscais:**

1. O aplicativo utiliza a base declarada ao Siconfi no arquivo `data/siconfi/despesas_oficiais.csv` (27 UFs, três funções e exercícios de 2021 a 2025, total de 405 registros no pacote).
2. O usuário escolhe UFs, exercício, funções e formato da síntese. `services/sumarizacao.py` consulta os registros validados e calcula os somatórios com `Decimal`, sem pedir contas ao modelo.
3. Combinações sem cobertura suficiente são identificadas e não são transformadas em zero. Os resultados enviados ao Qwen especificam que as três funções **não constituem o orçamento completo** e que os valores são nominais, declarados e não auditados pela aplicação.
4. `POST /ia/sintese_fiscal` devolve a explicação e também o **contexto calculado pelo Python**, que pode ser conferido pelo usuário. Inclui URLs das declarações de origem.

A síntese fiscal é uma extensão da automação textual: o Python converte dados estruturados em evidências textuais e o Qwen as transforma em explicações. Não foi integrada uma série populacional do IBGE; **não há indicadores per capita nesta base**.

## Engenharia de prompts

Três versões são mantidas em `services/engenharia_prompts.py`, com o **mesmo modelo e parâmetros de geração** para permitir comparação:

| Versão | Orientação principal | Propósito |
|---|---|---|
| `basico` | Resume o conteúdo no formato solicitado. | Obter uma referência simples. |
| `estruturado` | Acrescenta instruções para preservar informações centrais, ressalvas e evitar repetições. | Melhorar clareza e cobertura. |
| `fundamentado` | Acrescenta regras para não inventar fatos, não confundir amostra e dados declarados e não extrapolar os cálculos. | Reduzir afirmações sem suporte e aumentar rastreabilidade. |

Os formatos oferecidos são **resumo executivo**, **pontos principais** e **linguagem simples**. Documentos coletados são tratados como **dados externos não confiáveis**: as instruções enviadas ao modelo dizem para ignorar comandos eventualmente contidos no documento. Essas instruções não eliminam inteiramente os riscos de erro, omissão ou alucinação.

### Como realizar o experimento comparativo real

Com o Qwen e a FastAPI em execução no computador de desenvolvimento:

```powershell
.\.venv\Scripts\python.exe scripts/avaliar_prompts.py
```

O script escolhe um documento do catálogo e solicita três gerações reais, uma por versão de prompt, com o mesmo documento, formato e limite padrão de **384 novos tokens**. Grava os textos obtidos e as métricas em `resultados/avaliacao_prompts_local.json` — diretório ignorado pelo Git. **Há uma execução real registrada** em `documentacao/experimentos/avaliacao_prompts_final.json`, produzida em 23/11/2026 com 384 tokens de limite de geração. As notas humanas permanecem nulas no JSON; não foram inventadas. A execução utilizou temporariamente uma instrução de 150 a 180 palavras, posteriormente retirada do código padrão.

A avaliação deve comparar, mediante leitura do documento original: (1) fidelidade às fontes, de 0 a 5; (2) cobertura dos pontos principais, de 0 a 5; (3) clareza, de 0 a 5; e (4) quantidade de afirmações sem suporte. As três notas não devem ser preenchidas sem revisão humana. O script deixa esses campos nulos justamente para distinguir medição real de avaliação ainda pendente.

## Rotas e modelos

| Rota | Função | Carrega o Qwen? |
|---|---|---|
| `GET /ia/documentos` | Listar documentos locais coletados | Não |
| `POST /ia/resumir_documento` | Sintetizar documento com origem identificada | Sim |
| `POST /ia/sintese_fiscal` | Explicar indicadores calculados da base oficial | Sim |
| `GET /ia/health` | Estado do modelo | Não |
| `POST /processar_texto` | Resumo/explicação de texto livre (legado) | Sim |

Exemplo de entrada para sumarização documental:

```json
{
  "documento_id": "<id apresentado em GET /ia/documentos>",
  "modo": "executivo",
  "versao_prompt": "fundamentado",
  "max_novos_tokens": 384
}
```

Exemplo de entrada para síntese fiscal:

```json
{
  "ufs": ["SP", "GO", "BA"],
  "ano": 2025,
  "funcoes": ["Saúde", "Educação", "Segurança Pública"],
  "modo": "topicos",
  "versao_prompt": "fundamentado",
  "max_novos_tokens": 384
}
```

As respostas são validadas por `response_model` Pydantic em `api/schemas/sumarizacao.py`: modelo, texto, origem, fontes, versão do prompt, execução local, tokens e tempo. A rota fiscal também fornece os valores calculados usados como referência. Erros do serviço são convertidos em códigos HTTP: `404` para documento desconhecido, `422` para parâmetros inválidos ou texto acima da capacidade, `429` para GPU ocupada, `503` para ausência de modelo ou base inconsistente, `504` para tempo-limite e `500` para falha interna. O contrato de erro preserva `X-Request-ID`.

**Execução:** iniciar a FastAPI com `--workers 1`, seguida do Streamlit. A serialização das gerações foi preservada para reduzir o risco de estouro de VRAM. Uma solicitação hierárquica pode envolver mais de uma chamada sequencial ao modelo; documentos grandes podem demorar e ultrapassar o tempo de espera do cliente HTTP.

## Testes e limites de comprovação

Os testes automatizados verificam catálogo, procedência, formatos, validação de entrada, 404/422/429/503/504, contabilidade fiscal exata, exclusão de somatórios incompletos, divisão em fragmentos e integração HTTP, **substituindo apenas a geração do Qwen por um resultado controlado**. Isso permite testar a aplicação sem ocupar a GPU, mas não comprova a qualidade do texto produzido pelo modelo.

Para o teste real, com a FastAPI já ligada:

```powershell
.\.venv\Scripts\python.exe scripts/teste_sumarizacao_http_real.py --fiscal
```

O teste consulta um documento real do catálogo e, se `--fiscal` estiver presente, também sintetiza um recorte fiscal. Essas chamadas **executam o Qwen na GPU**. Devem ser realizadas no computador com o modelo instalado antes de afirmar que a nova funcionalidade foi validada integralmente na RTX 4060.

**Limitações explícitas:** este recurso não é um RAG semântico de perguntas livres, não oferece memória conversacional, não acessa novos sites durante a geração e não substitui auditoria, validação contábil ou checagem humana das conclusões. As quatro fontes institucionais atualmente catalogadas são textos relativamente curtos; não representam um corpus amplo de relatórios. A interface e os procedimentos de sumarização hierárquica permitem ampliação posterior das fontes, sujeita aos limites de tokens e tempo da execução local.
