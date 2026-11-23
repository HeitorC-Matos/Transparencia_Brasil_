# Dashboard final integrado — Transparência Brasil

## Objetivo

O dashboard da página **Gastos públicos** integra coleta, tratamento, exploração estatística e a geração sob demanda de explicações por LLM. Foi concebido para demonstrar o ciclo completo de Ciência de Dados, com enfoque em **governança pública e transparência** (ODS 16). Não realiza inferências de eficiência, sustentabilidade ambiental ou qualidade dos serviços.

## Fluxo de dados e rastreabilidade

| Etapa | Implementação | Evidência |
|---|---|---|
| Coleta fiscal | `scripts/coletar_siconfi.py` consulta a API do Siconfi | `data/siconfi/despesas_oficiais.csv` e `manifesto.json` |
| Coleta documental | `coleta_web.py` (Requests/Beautiful Soup) e `coleta_selenium.py` | `data/conteudo_web.csv` e `data/conteudo_selenium.csv` |
| Preparação | Normalização, validação do RREO, exclusão de duplicidades, corpus textual | `services/siconfi.py`, `services/consulta_oficial.py`, `preparar_llm.py` |
| Análise | Recortes por ano, UF e função; rankings e séries históricas | `utils/estatisticas_oficiais.py` e `utils/dashboard_final.py` |
| Inteligência artificial | Síntese fiscal, resumos documentais e consulta em linguagem natural | Qwen3-4B-Instruct-2507 via FastAPI, acionado pelo usuário |
| Apresentação | Gráficos, indicadores, fontes, tabelas e exportação | `pages/4_Estatisticas.py`, `utils/dashboard_ui.py` e `utils/estatisticas_ui.py` |

**Não há mistura de bases:** `data/amostra_dados.csv` é apenas ilustrativo e não aparece no dashboard. A página ilustrativa antiga foi retirada do menu, mas seu código e seus testes permanecem. O novo dashboard **Gastos públicos** usa exclusivamente os registros oficiais recebidos pelos endpoints `GET /dados-oficiais` e `GET /dados-oficiais/status`. O catálogo documental vem de `GET /ia/documentos`.

A base publicada nesta versão contém **27 UFs, 2021–2025 e três funções** (Educação, Saúde e Segurança Pública), totalizando 405 combinações UF/ano/função. Esses números descrevem a cobertura do arquivo distribuído, não uma garantia de que futuras atualizações terão a mesma cobertura.

## Organização final do menu

A página **App** apresenta a finalidade do projeto, o ODS 16, o ciclo de Ciência de Dados e as opções de navegação, **sem reproduzir gráficos**. O painel passou da App para **Gastos públicos** (antes Estatísticas), com uma única seleção de filtros para gráficos e análises detalhadas. A aba antiga de Gastos públicos, baseada em valores ilustrativos de SP, GO e BA, não está no menu. A coleta e a amostra histórica não foram excluídas do código.

## Interatividade

O usuário seleciona UFs (uma, várias ou todas), ano e funções. A página apresenta:

- Subtotal das **funções selecionadas**, nunca apresentado como despesa total estadual; apenas UFs com todas as funções selecionadas são somadas.
- Gráfico comparativo por função, ranking das dez maiores UFs do recorte e evolução histórica nominal.
- Cobertura (registros presentes/esperados), indicação explícita de lacunas, tabela e exportação CSV com URLs de origem.
- Botão **Explicar os gráficos selecionados com Qwen**, que produz explicação contextualizada dos mesmos filtros.
- Aba **Análises detalhadas** com as seis visualizações anteriores, usando os mesmos filtros de UF, ano e funções; aba **Insights com Qwen** com seleção do formato, estratégia de prompt e perguntas em linguagem natural.
- A sumarização de documentos coletados permanece no **Assistente IA**, sem duplicar sua interface no painel fiscal.
- Aba **Fontes e critérios**, detalhando os métodos e a procedência.

Os pedidos de geração são acionados por botão; **abrir a página de Gastos públicos não carrega automaticamente os pesos do modelo**. As respostas fiscais são calculadas no backend e apenas explicadas pelo Qwen; o resultado gerado é identificado como IA e inclui contexto e fontes. Uma explicação anterior não aparece como atual após alteração dos filtros fiscais. Falhas do modelo não eliminam os gráficos oficiais.

No novo dashboard, o **prompt Estruturado** é a seleção inicial da interface, em consonância com a execução comparativa registrada no projeto. O Básico e o Fundamentado continuam disponíveis; seus textos originais não foram alterados. O limite padrão de geração permanece **384 tokens**. O experimento de engenharia de prompts da Tarefa 2 e seus resultados foram preservados em `documentacao/experimentos/avaliacao_prompts_final.json` e `documentacao/AVALIACAO_EXPERIMENTAL_PROMPTS.md`.

## Escopo e limitações

Os dados fiscais representam **despesas liquidadas até o 6º bimestre**, RREO Anexo 02, em valores nominais, excluídas as intraorçamentárias. Não incluem despesas municipais, todas as funções de governo nem valores deflacionados. O dashboard não apresenta despesa por habitante porque não existe série populacional IBGE integrada à base oficial. A participação percentual quando mostrada em Gastos públicos se refere somente à soma das três funções, não ao orçamento total.

As declarações não foram auditadas independentemente por esta aplicação. Mais despesa não significa melhor gestão ou resultados sociais. Resumos do Qwen podem incluir afirmações imprecisas; o usuário deve conferir as fontes e evidências exibidas.

## Execução e validação

FastAPI:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Streamlit (outro terminal):

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Verifique as fontes pelo HTTP sem carregar o modelo:

```powershell
.\.venv\Scripts\python.exe scripts/verificar_dashboard.py
```

Execute os testes automatizados:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Validação manual informada pelo autor:** o autor executou a aplicação completa em seu computador, verificou a navegação e os recursos integrados, incluindo o Qwen local, e relatou **não ter encontrado problemas**. A verificação manual foi realizada no ambiente real de uso; não é uma avaliação formal com terceiros. Para reproduzir os testes, recomenda-se: (1) abrir **Gastos públicos** com GO, BA e SP/2025/Educação; (2) conferir os gráficos e subtotais na base oficial; (3) solicitar a explicação com Qwen; (4) resumir um documento coletado; (5) consultar uma despesa com pergunta livre e verificar os valores do Python.

A bateria automatizada de **243 testes aprovados, oito avisos e nenhuma falha** verifica dados, API e a renderização simulada, **sem carregar os pesos do Qwen**. O experimento real de prompts e a validação manual relatada pelo autor constituem evidências distintas dessa bateria.


## Demonstração de governança e ODS 16

Para evidenciar o uso conjunto de dados da API e de coleta por web scraping, pode-se selecionar as despesas de Educação de 2025 em **Gastos públicos** e solicitar ao Qwen uma explicação dos valores calculados. Depois, em **Assistente IA → Documentos coletados**, seleciona-se o texto institucional sobre o **ODS 16** e solicita-se um resumo com fonte identificada. A demonstração relaciona a consulta pública e a explicação em linguagem acessível às metas **16.6** (instituições responsáveis e transparentes) e **16.10** (acesso à informação), no componente **Governança** do ESG. Os dados disponíveis não sustentam uma nota de ESG, uma avaliação de eficiência ou uma relação causal com resultados sociais.
