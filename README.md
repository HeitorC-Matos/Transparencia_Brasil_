# Transparência Brasil — TP3 

Continuação dos TPs 1 e 2, associada ao **ODS 16**. Mantém os três estados **SP, GO e BA**, as funções **Educação, Saúde e Segurança Pública** e os **9 registros fiscais ilustrativos** de 2025. Os valores da amostra não foram auditados em Siconfi/IBGE; **não são totais governamentais oficiais**.

## Recursos entregues

- **Streamlit multipágina:** início, gastos, conteúdo Web, arquivos, estatísticas, FastAPI e preparação para IA. Menu automático na barra lateral por `pages/`.
- **FastAPI integrada de verdade:** as páginas de gastos, estatísticas e conteúdo Web fazem requisições HTTP (`GET /despesas`, `/estatisticas` e `/conteudo-web`); a página de API oferece filtros e **formulário POST /despesas** para cadastro manual. Indicador de saúde `GET /health`.
- **Coleta Beautiful Soup:** duas páginas originais + uma nova URL oficial da **CGU** sobre transparência pública; parser, timeout, tentativas e CSV/TXT.
- **Selenium:** `coleta_selenium.py` acessa uma página oficial sobre obrigações de transparência, aguarda o texto renderizado e grava um **CSV/TXT separado** quando o acesso funcionar.
- **Preparação LLM:** JSONL com trechos, URL e metadados. Não há chamada a modelos nesta etapa.
- **Testes:** validações da API, cliente HTTP, GET/POST, scraping, Selenium simulado, transformação e preparação para LLMs.

> **Proveniência da nova fonte:** `data/conteudo_web.csv` inclui um terceiro registro sobre a CGU, preparado a partir de uma consulta verificável ao conteúdo público da página, com método `resumo_documentado_por_consulta_web`. Esse registro **não é apresentado como extração Beautiful Soup executada**. Quando você executar `python coleta_web.py` com acesso à Internet, o programa buscará o HTML da página e substituirá o resumo pela extração real, identificada por `requests+beautifulsoup` e data UTC. O Selenium também depende de Internet e de um WebDriver compatível para coleta real; testes com navegador simulado **não substituem** essa execução.

## Estrutura resumida

```text
Transparencia_Brasil_TP3/
├── app.py                         # Página inicial e menu do Streamlit
├── pages/                        # Seis páginas da interface
├── api/main.py                   # API FastAPI: GET e POST
├── utils/api_client.py           # Cliente HTTP usado pelas páginas Streamlit
├── utils/dados.py                # Fontes e conciliação de CSVs
├── coleta_web.py                 # Requests + Beautiful Soup (3 URLs)
├── coleta_selenium.py            # Navegador Selenium (1 URL oficial)
├── preparar_llm.py               # JSONL e manifesto
├── data/
│   ├── amostra_dados.csv          # 9 linhas do TP2, intactas
│   ├── conteudo_web.csv           # 3 fontes (2 TP2 + 1 registro documentado)
│   ├── conteudo_web.txt
│   ├── conteudo_selenium.csv      # Só é criado após coleta Selenium bem-sucedida
│   └── llm/
├── tests/
├── documentacao/
│   ├── PROJECT_CHARTER.md
│   ├── DATA_SUMMARY_REPORT.md
│   ├── API.md
│   ├── PREPARACAO_LLM.md
│   └── RELATORIO_TESTES.md
├── requirements.txt
└── .gitignore
```

## 1. Instalação

Recomendado **Python 3.11 ou 3.12** (mínimo 3.10). No terminal na raiz do projeto:

```bash
python -m venv .venv
```

Windows PowerShell: `.\.venv\Scripts\Activate.ps1` (caso necessário, execute `Set-ExecutionPolicy -Scope Process RemoteSigned`). Linux/macOS: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
```

A dependência `selenium` está no `requirements.txt`. É necessário um Chrome/Chromium e um ChromeDriver compatível; nas versões recentes o Selenium Manager tenta obter o driver automaticamente. Se não conseguir, instale o driver e configure `TP3_CHROMEDRIVER_PATH`; se o executável do navegador não for encontrado, configure `TP3_CHROMIUM_BIN`.

## 2. Executar API e aplicação (dois terminais)

**Terminal 1 — FastAPI:**

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Documentação interativa: http://127.0.0.1:8000/docs. Teste de saúde: http://127.0.0.1:8000/health.

**Terminal 2 — Streamlit:**

```bash
streamlit run app.py
```

Acesse http://localhost:8501. Escolha **Gastos públicos**, **Estatísticas**, **Conteúdo da Web** ou **API FastAPI** e confirme a mensagem de integração HTTP. Na página **API FastAPI**, faça GET com filtros e envie um novo registro no formulário POST. Ao selecionar origem `manual`, o novo registro aparece na tabela depois de atualizar a página. O CSV original não é alterado.

Se a API estiver indisponível, as páginas de consulta exibem **aviso explícito** e podem mostrar dados locais para a navegação continuar; **esse modo offline não conta como integração ativa**. A página de API não simula POST.

Se a API for hospedada em outra URL, configure antes de iniciar o Streamlit: variável de ambiente `TP3_API_URL` (ex.: `http://127.0.0.1:8000`). **A aplicação Streamlit não inicia automaticamente a API.**

## 3. Coletar mais dados da Web

### Requests + Beautiful Soup (fonte CGU acrescentada)

```bash
python coleta_web.py
```

Consulta as páginas do **ODS 16**, **Siconfi** e **CGU Transparência Pública** e atualiza `data/conteudo_web.csv` e `.txt`. Em caso de falha, a versão anterior de cada URL é preservada; o script sinaliza a falha, sem inventar uma nova coleta. URLs verificadas:

- https://brasil.un.org/pt-br/sdgs/16
- https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos
- https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica

### Selenium (coleta opcional, implementação existente)

```bash
python coleta_selenium.py
```

Abre o portal oficial de **Informações obrigatórias / Transparência Ativa** via Chromium/Chrome em modo headless, aguarda parágrafos no DOM e grava `data/conteudo_selenium.csv` e `data/conteudo_selenium.txt`. A coleta falha sem gerar dados fictícios caso o site ou o navegador não estejam disponíveis. Após execução real, o conteúdo Selenium é exposto também por `GET /conteudo-web` e aparece na página Web do Streamlit.

**Nota metodológica:** Selenium é utilizado para cumprir a rubrica de coleta com navegador. A página selecionada não foi comprovada como dependente de JavaScript; a mesma informação pode estar disponível em HTML estático. O enunciado permite Beautiful Soup quando não há essa dependência. Não confundir a existência do script com execução externa comprovada.

## 4. Preparar os dados para IA

```bash
python preparar_llm.py
```

Gera `data/llm/documentos.jsonl` e `manifesto.json`, incorporando as fontes Web existentes e a amostra ilustrativa. No pacote: **12 documentos** (3 Web e 9 fiscais), sem execução de LLM. Se Selenium tiver feito coleta real, execute novamente o comando para incluir o novo texto.

## 5. Testes

```bash
python -m pytest -q
```

Testes de API e HTTP independem dos portais externos, usando TestClient, ambiente temporário e navegador simulado. Reproduza também o teste real de rede local: `python -m scripts.teste_http_real` — ele sobe Uvicorn numa porta temporária, consulta GET e realiza POST por HTTP. Veja [Relatório de Testes](documentacao/RELATORIO_TESTES.md). **A abertura visual do Streamlit e o acesso real ao portal pelo Selenium exigem validação no computador com as dependências instaladas.**

## 6. GitHub

Copie os arquivos do ZIP para o clone já existente, mantendo o diretório `.git`, e execute:

```bash
git status
git add .
git commit -m "TP3 - integracao Streamlit FastAPI e coletores Web Selenium"
git push origin main
```

Repositório: https://github.com/HeitorC-Matos/Transparencia_Brasil_

Registros feitos via POST são ignorados pelo Git; **não publique a API POST sem autenticação ou persistência adequada**.

**Documentos:** [Project Charter](documentacao/PROJECT_CHARTER.md), [Data Summary Report](documentacao/DATA_SUMMARY_REPORT.md), [Guia da API](documentacao/API.md), [Preparação LLM](documentacao/PREPARACAO_LLM.md).
