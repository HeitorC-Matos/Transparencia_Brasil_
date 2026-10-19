# Data Summary Report — Transparência Brasil (TP3, revisão das rubricas)

## 1. Visão geral dos conjuntos

| Conjunto | Arquivo | Quantidade incluída na entrega | Origem e confiabilidade |
|---|---|---:|---|
| Amostra fiscal TP1/TP2 | `data/amostra_dados.csv` | 9 linhas | Amostra **ilustrativa**, valores não auditados |
| Catálogo de conteúdo Web | `data/conteudo_web.csv` e `.txt` | 3 registros | 2 textos originais TP2 + 1 resumo documentado da CGU |
| Selenium | `data/conteudo_selenium.csv` e `.txt` | 0 nesta entrega | Criados somente após coleta real com navegador |
| Cadastros manuais | `data/registros_manuais.csv` | 0 inicialmente | Apenas POST válido; origem `manual`, não verificada |
| Preparação LLM | `data/llm/documentos.jsonl` e `manifesto.json` | 12 documentos | 3 textos Web + 9 descrições fiscais, sem executar LLM |

## 2. Base fiscal original

- **Unidades federativas:** SP, GO e BA.
- **Período:** 2025.
- **Funções:** Educação, Saúde e Segurança Pública.
- **Colunas:** `estado`, `sigla`, `ano`, `funcao`, `valor_despesa`, `populacao`, `fonte_fiscal`, `fonte_populacao`.
- **Referências declaradas:** Siconfi para fiscal e IBGE para população.

**Importante:** o material herdado não inclui as consultas/IDs de cada valor em Siconfi ou IBGE, nem auditoria independente. As referências declaradas não comprovam os valores. O CSV original está **preservado byte a byte** e não é atualizado pelo POST. Totais e indicadores per capita são úteis apenas para demonstração técnica.

## 3. Textos de páginas públicas (Beautiful Soup)

| URL oficial | Papel no projeto | Situação no pacote |
|---|---|---|
| https://brasil.un.org/pt-br/sdgs/16 | Contexto sobre ODS 16 | Registro herdado do TP2 |
| https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos | API de dados fiscais do Siconfi | Registro herdado do TP2 |
| https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica | Nova fonte para contextualizar transparência e dados abertos | **Resumo documentado da página**, não extração Beautiful Soup comprovada |

`coleta_web.py` contém as três URLs e usa Requests com retries, timeout, Beautiful Soup para título/parágrafos, remoção de menus/scripts, deduplicação de parágrafos e persistência CSV/TXT. **Uma execução online bem-sucedida** define `data_coleta` UTC e `metodo=requests+beautifulsoup`. Na indisponibilidade de rede, o programa conserva registros anteriores e informa a falha. No ambiente desta entrega, os portais não puderam ser acessados diretamente pelo script: por transparência, o novo registro CGU está rotulado `resumo_documentado_por_consulta_web`, e sua data de scraping não foi inventada.

**Fonte da informação resumida:** página oficial da Controladoria-Geral da União sobre *Transparência Pública e Dados Abertos*, consultada por mecanismo de pesquisa Web. O resumo é uma paráfrase curta, não uma transcrição extensiva da página. Não foi extraído nenhum novo dado numérico fiscal dessa URL.

**Colunas Web:** `titulo`, `url`, `texto`, `data_coleta` e `metodo`; compatibilidade preservada com os três campos originais do TP2. A API `GET /conteudo-web` devolve o catálogo e inclui arquivos Selenium válidos, caso existam.

## 4. Coleta por Selenium

**Script:** `coleta_selenium.py`.

**URL oficial configurada:** https://www.gov.br/acessoainformacao/pt-br/assuntos/transparencia-ativa/informacoes-obrigatorias.

**Fluxo implementado:** Selenium WebDriver inicia Chromium/Chrome headless, navega para a página, utiliza `WebDriverWait` com verificação de parágrafos no DOM, obtém `page_source`, extrai título/texto pelo parser compartilhado com Beautiful Soup e grava `data/conteudo_selenium.csv/.txt`, com `metodo=selenium+chromium` e data UTC. Havendo erro, nenhuma coleta é alegada ou fabricada. A página foi selecionada por relevância ao tema de transparência e pelo conteúdo institucional; **não há afirmação de que o portal só funcione com JavaScript**.

**Validação disponível nesta entrega:** testes automatizados com navegador simulado verificam navegação, espera, extração, gravação e rejeição de página vazia. **Validação pendente:** execução Selenium WebDriver real contra o portal, pois o ambiente atual não dispõe de Selenium/ChromeDriver e acesso direto à Internet. Rodar `python coleta_selenium.py` em máquina configurada para obter evidência real.

## 5. FastAPI, consumo no Streamlit e entrada manual

O fluxo técnico é:

`CSV original → FastAPI GET /despesas → requests (utils/api_client.py) → Streamlit / Gráficos`

`Formulário Streamlit → requests POST /despesas → FastAPI/Pydantic → registros_manuais.csv`

As páginas de Estatísticas e Conteúdo Web consultam também GET `/estatisticas` e GET `/conteudo-web`, respectivamente. O cliente faz paginação para reunir todos os resultados; erro HTTP ou API desligada aparece claramente na interface. Para garantir consulta didática sem backend, algumas páginas possuem fallback de visualização local **rotulado como offline**.

O POST aceita UF SP/GO/BA, ano 2000–2100, função enumerada, valor finito não negativo e população positiva. A API responde 201 e adiciona `id_registro`, `origem=manual` e `data_cadastro`. Os novos dados não contaminam análises da amostra, cujo filtro é `origem=amostra_academica`.

## 6. Preparação LLM

O comando `python preparar_llm.py` consolida o catálogo Web disponível (incluindo Selenium, quando coletado de verdade) e descreve a amostra de nove linhas em documentos com `id`, `tipo`, `origem`, `conteudo`, `metadados`. Os textos do Web preservam `url`, título e **método** de aquisição, distinguindo síntese documentada de scraping automatizado. Cada registro fiscal possui sinalização de não verificado. Dados manuais não entram no JSONL.

**Usos futuros:** resumos com citação de fonte, Q&A/RAG, geração de relatórios de demonstração. Sentimentos exigiriam outra base com opinião textual; não se deduzem sentimentos de tabelas fiscais ou textos institucionais.

## 7. Problemas e limitações

- Comparações acadêmicas **não** substituem análises fiscais auditadas.
- Terceiro texto Web consultado/documentado, mas sem scraping HTTP executado nesta máquina.
- A coleta Selenium só pode ser declarada **efetivamente executada** após gerar os seus CSV/TXT numa máquina com webdriver/rede.
- URLs podem mudar, apresentar rate limits ou bloquear automação; os scripts mostram o erro, não geram dados fictícios.
- API POST é local, sem autenticação e com arquivo CSV; é inadequada para exposição pública.
- Um LLM futuro deve usar fontes citadas e ser avaliado por fidelidade.

## 8. Reprodutibilidade

1. `pip install -r requirements.txt`
2. `uvicorn api.main:app --reload` (terminal 1)
3. `streamlit run app.py` (terminal 2)
4. `python coleta_web.py` (Internet necessária para extração online)
5. `python coleta_selenium.py` (Internet, Selenium, Chrome/Chromium e driver)
6. `python preparar_llm.py` (atualiza corpus após coletas)
7. `python -m pytest -q` (testes automatizados offline)

Consultar `documentacao/RELATORIO_TESTES.md` para evidências e roteiro manual.
