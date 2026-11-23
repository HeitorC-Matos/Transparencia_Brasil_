# Transparência Brasil

Aplicação de **Ciência de Dados e inteligência artificial** para consultar, comparar e explicar despesas públicas dos estados e do Distrito Federal. O projeto combina **Streamlit**, **FastAPI**, dados oficiais do **Siconfi/Tesouro Nacional** e o modelo local **Qwen3-4B-Instruct-2507**.

O problema que motivou o trabalho é a dificuldade de encontrar, comparar e compreender dados fiscais divulgados em formatos técnicos. A solução apresenta gráficos e tabelas interativas, deixa visíveis os critérios e as fontes e oferece resumos e explicações em linguagem simples. Seu alinhamento principal é com o **ODS 16** (especialmente as metas 16.6 e 16.10) e com a dimensão de **Governança (G)** do ESG: acesso à informação, transparência e possibilidade de acompanhamento das despesas. **O sistema não avalia a eficiência dos governos nem comprova efeitos ambientais ou sociais das despesas.**

## 1. O que o usuário encontra

| Página visível | Finalidade |
|---|---|
| **App** | Apresentação resumida do projeto, problema, metodologia e navegação. |
| **Gastos públicos** | Dashboard nacional: filtros por UF, exercício e função; gráficos, ranking, série histórica, comparações, estatísticas detalhadas e insights com Qwen. |
| **Dados oficiais** | Consulta dos registros consolidados do Siconfi, cobertura, critérios, fontes e exportação. |
| **Conteúdo da Web** | Textos institucionais obtidos por Beautiful Soup e Selenium, com metadados. |
| **API FastAPI** | Contratos HTTP, documentação das rotas e mensagens de erro. |
| **Assistente IA** | Perguntas fiscais e sobre o ODS 16, categoria própria de Governança ESG, síntese fiscal, resumo de documentos coletados e texto livre. |

A página **App não repete o dashboard**. As visualizações estatísticas e os insights relacionados aos filtros ficam em **Gastos públicos**. O **Assistente IA** concentra a interação textual. Os recursos históricos da primeira amostra continuam armazenados para demonstração e testes, mas não aparecem como uma segunda página de despesas.

## 2. O ciclo de Ciência de Dados

O projeto segue o **Team Data Science Process (TDSP)**, do entendimento do problema à aceitação da solução:

1. **Entendimento do problema:** facilitar a compreensão e comparação de despesas públicas, com foco em transparência e governança.
2. **Coleta e compreensão:** obter despesas do Siconfi por API e reunir documentos institucionais por Requests/Beautiful Soup e Selenium, registrando origem e data de coleta.
3. **Preparação e análise:** padronizar dados por UF, ano e função; verificar cobertura e duplicidades; calcular rankings, diferenças, percentuais e evolução histórica em Python.
4. **Modelagem e IA:** recuperar documentos coletados, construir prompts, resumir textos e explicar resultados estatísticos com o Qwen local. Os cálculos fiscais não são delegados ao modelo.
5. **Implantação e aceitação:** apresentar tudo no Streamlit por meio da FastAPI, executar testes automatizados e realizar verificações manuais na aplicação.

Os artefatos **[Project Charter](documentacao/PROJECT_CHARTER.md)** e **[Data Summary Report](documentacao/DATA_SUMMARY_REPORT.md)** descrevem as decisões, o tratamento dos dados e os limites do escopo. O documento integrado pode ser consultado em [PDF](documentacao/TDSP_ARTEFATOS_REVISADOS.pdf) ou [DOCX](documentacao/TDSP_ARTEFATOS_REVISADOS.docx). A [proposta original](documentacao/historico/proposta_original.pdf) está preservada para comparação.

## 3. Dados oficiais do Siconfi e amostra ilustrativa

### Base fiscal utilizada pelo dashboard

A coleta em `scripts/coletar_siconfi.py` utiliza a **API de Dados Abertos do Siconfi**. O recorte é o **RREO, Anexo 02 — Despesas por Função/Subfunção**, **6º bimestre** de cada exercício, com a coluna **DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)**. São selecionadas as linhas das funções **Segurança Pública (06), Saúde (10) e Educação (12)**, sem as intraorçamentárias.

A base incluída no repositório contém:

| Cobertura | Quantidade |
|---|---:|
| Unidades da Federação | **27** (26 estados e DF) |
| Exercícios | **5** (2021–2025) |
| Funções fiscais | **3** |
| Combinações UF × ano × função | **405** |

Os dados estão em `data/siconfi/despesas_oficiais.csv`; `data/siconfi/manifesto.json` descreve os critérios da extração e a cobertura. Há campos de origem, data e identificadores para rastreabilidade. A validação estrutural identificou 405 registros, sem duplicidades nas combinações e sem pendências no manifesto; **essa conferência não equivale a auditoria independente dos números informados pelos entes ao Siconfi**.

Os gráficos exibem valores **nominais de despesas liquidadas**, não necessariamente investimentos de capital. Quando a página mostra o **total** de uma UF, trata-se do **subtotal das funções selecionadas**, e não de todas as funções ou do orçamento inteiro daquele governo. Percentuais de composição também consideram apenas essas funções. Registros ausentes nunca são convertidos automaticamente em zero. A série populacional oficial do IBGE e a correção monetária pelo IPCA **não foram integradas**, de modo que não há indicador oficial por habitante nem comparação em valores reais corrigidos da inflação.

A [metodologia completa](documentacao/DADOS_OFICIAIS_SICONFI.md) registra as regras do RREO; o [guia de estatísticas](documentacao/ESTATISTICAS_NACIONAIS.md) descreve os cálculos. Os arquivos brutos de cache não precisam ser publicados: o código de coleta, o CSV consolidado e o manifesto permitem examinar e reproduzir o processo.

### Amostra do início do desenvolvimento

O arquivo `data/amostra_dados.csv` possui **nove registros ilustrativos de 2025**, relativos a SP, GO e BA. A amostra não foi comprovada por uma coleta fiscal oficial ou pelo IBGE; por isso **não alimenta o dashboard oficial**. Foi mantida, assim como seu módulo de cálculos e testes, para preservar o desenvolvimento anterior e verificar regressões. Os cadastros manuais da rota `POST /despesas` ficam isolados em `data/registros_manuais.csv`, que não integra o ZIP de publicação.

## 4. Coleta de textos e preparação para a IA

- `coleta_web.py`: Requests e **Beautiful Soup** para três páginas institucionais, relacionadas ao **ODS 16/ONU**, à **API do Siconfi/Tesouro Nacional** e à **transparência/CGU**; arquivos `data/conteudo_web.csv` e `.txt`.
- `coleta_selenium.py`: **Selenium com Chromium** para um documento governamental sobre transparência ativa; arquivo `data/conteudo_selenium.csv` e `.txt`. A coleta armazenada ocorreu em **19/10/2026**; os testes automatizados do coletor usam navegador simulado.
- `preparar_llm.py`: estrutura conteúdos em `data/llm/documentos.jsonl`, com **16 fragmentos** registrados no manifesto (sete extraídos das fontes da Web e nove descrições da amostra ilustrativa). Esse preparador não executa a IA sozinho.

O catálogo de sumarização utiliza os **quatro documentos institucionais coletados**, mantendo título, URL, origem, data e texto. Para conteúdos longos, a aplicação pode produzir resumos por trechos e depois consolidá-los. A utilização documental não depende de copiar manualmente um texto para o modelo; também não há, nesta versão, **RAG vetorial** nem memória conversacional persistente.

## 5. Dashboard e análises estatísticas

A página **Gastos públicos** consulta a FastAPI para carregar os registros oficiais. Os filtros compartilhados permitem selecionar **uma, várias ou todas as UFs**, um exercício de 2021 a 2025 e as funções desejadas. O painel oferece indicadores resumidos, barras de despesas por função, classificação das UFs e evolução nominal. As análises detalhadas incluem **distribuição percentual, rankings e regiões, comparação direta entre duas UFs, perfil individual, evolução histórica, matriz e estatísticas descritivas** (média, mediana, mínimo, máximo e amplitude). Também é possível exportar registros do recorte em CSV.

As agregações só são apresentadas quando há cobertura suficiente; a interface informa a fonte e as lacunas. No próprio dashboard, o usuário pode clicar em **Explicar os gráficos selecionados com Qwen**. Os valores já calculados pelo Python são enviados ao modelo somente quando a explicação é solicitada; se o Qwen falhar, os gráficos e números permanecem disponíveis.

Consulte o [guia do dashboard](documentacao/DASHBOARD_INTEGRADO.md) e o [guia das perguntas fiscais](documentacao/PERGUNTAS_DADOS_OFICIAIS.md).

## 6. Inteligência artificial: funcionalidades implementadas

A aplicação utiliza um **LLM local** para transformar conteúdos coletados e indicadores calculados em respostas compreensíveis. O **Python é a fonte dos números**; o Qwen não pesquisa o orçamento nem calcula rankings por conta própria.

| Funcionalidade | O que acontece |
|---|---|
| **Documentos coletados** | Escolha de um documento obtido por scraping; resumo executivo, tópicos ou explicação simplificada, com fonte identificada. |
| **Síntese fiscal** | Filtros de UFs, ano e funções; Python calcula os indicadores e o Qwen produz uma síntese textual. |
| **Perguntar aos dados** | Perguntas sobre despesas oficiais **e sobre o projeto, ODS 16 e Governança ESG**. Identifica o assunto automaticamente e usa a fonte correspondente. |
| **ODS 16 e Governança** | **Categoria dedicada**: perguntas prontas ou personalizadas sobre a relação do Transparência Brasil com as metas **16.6 e 16.10**, transparência e acesso à informação; explicações do Qwen com fontes verificáveis. |
| **Insights em Gastos públicos** | Explicação contextualizada dos gráficos e valores que já estão sendo visualizados. |
| **Texto livre** | Resumo ou explicação do texto digitado; **não consulta automaticamente** a base fiscal. |

A interpretação de perguntas fiscais é restrita a operações controladas, sem SQL escrito pelo modelo. Quando uma pergunta usa a expressão “investiu”, a resposta esclarece que o indicador disponível é **despesa liquidada**. Na rota de perguntas, a resposta numérica continua disponível sem o Qwen; a explicação adicional é opcional.

A engenharia de prompts possui três versões: **Básico**, **Estruturado** e **Fundamentado**, com três formatos de saída. O limite padrão é de **384 novos tokens** (máximo, não obrigação de gerar 384). `scripts/avaliar_prompts.py` registra as respostas, entradas, saídas e durações. No [experimento real](documentacao/experimentos/avaliacao_prompts_final.json) com um documento do Siconfi, os prompts Básico e Estruturado concluíram as respostas; o Fundamentado chegou ao limite de 384 tokens e foi interrompido. Trata-se de **uma execução por configuração**, insuficiente para afirmar superioridade estatística de qualquer prompt. A [análise experimental](documentacao/AVALIACAO_EXPERIMENTAL_PROMPTS.md) discute fidelidade, cobertura e clareza, sem atribuir notas automáticas.

### ODS 16 e Governança ESG: integração no assistente

A aplicação possui agora uma categoria própria **Assistente IA → ODS 16 e Governança**, além de reconhecer perguntas institucionais em **Assistente IA → Perguntar aos dados**. Ao perguntar **“Como o Transparência Brasil se relaciona com o ODS 16?”**, a FastAPI localiza o documento da ONU Brasil coletado por Beautiful Soup e lê o contexto documentado do projeto. As metas **16.6** (instituições responsáveis e transparentes) e **16.10** (acesso público à informação) são fornecidas ao **Qwen local**, que redige uma explicação fundamentada. A resposta apresenta também as fontes, o critério e as limitações; sem GPU, o sistema retorna uma explicação factual preparada em Python. **Não afirma que a aplicação mede o cumprimento do ODS ou que maiores despesas representam mais eficiência.** Consulte o [guia da integração ODS 16](documentacao/ODS16_E_GOVERNANCA_INTERATIVA.md).

### Por que escolhemos o Qwen3-4B-Instruct-2507 em vez de outro modelo?

A escolha foi baseada **na tarefa e no computador realmente utilizado**, e não apenas no nome ou popularidade de um LLM. Precisávamos de um modelo que gerasse resumos em português, seguisse instruções variadas, explicasse indicadores fornecidos pelo Python e funcionasse **localmente**, sem custos de chamadas a uma API de IA hospedada a cada pergunta.

**Modelo e características.** Escolhemos [`Qwen/Qwen3-4B-Instruct-2507`](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), da equipe Qwen, publicado no **Hugging Face**, com **4,0 bilhões de parâmetros**, arquitetura generativa causal e ajuste para seguir instruções. A versão *Instruct-2507* trabalha no modo não deliberativo (*non-thinking*), adequado a resumos e explicações diretas. O cartão oficial declara contexto nativo de até **262.144 tokens**, mas **a nossa aplicação limita a entrada a 2.048 tokens** para preservar a GPU; não prometemos a janela máxima do modelo na máquina local.

**Hardware e VRAM.** A instalação utilizada possui **16 GB de RAM** e uma **NVIDIA GeForce RTX 4060 Laptop com aproximadamente 8 GB de VRAM (8.188 MiB reportados)**. Quatro bilhões de pesos em 16 bits exigiriam aproximadamente **8 GB decimais só para os pesos**, antes de cache, ativações e demais estruturas; isso seria muito apertado para a VRAM disponível. Por essa razão, em `services/llm_service.py`, o carregamento utiliza **bitsandbytes em 4 bits, tipo NF4**, **dupla quantização** e **cálculos em float16**. A estimativa ideal de 4 bits é perto de **2 GB decimais de pesos**, mas o consumo total é maior por causa das estruturas adicionais. Não se afirma uma medição exata de VRAM que não foi registrada. Também limitamos a 2.048 tokens de entrada, uma geração simultânea e um processo da API, reduzindo risco de esgotamento de memória.

**Comparação com alternativas.** Um **BERT-base** (cerca de **110 milhões de parâmetros**) é especialmente apropriado a tarefas de representação, classificação ou extração, mas **não é um gerador conversacional livre** como o necessário para explicar os resultados. O **T5-small** (cerca de **60 milhões de parâmetros**) **é generativo** e poderia resumir textos, sobretudo com ajuste adequado, mas sua capacidade e formato de treinamento não seriam a escolha mais direta para combinar instruções abertas, português, sumarização e explicações fiscais nesta aplicação. Já um modelo **maior**, como um LLM de **7 bilhões de parâmetros**, exigiria mais memória para pesos, cache e execução; poderia funcionar com outras configurações de quantização, porém com maior risco operacional e possível aumento de latência em uma GPU de 8 GB. **Não realizamos benchmark entre esses modelos**: a comparação é uma justificativa técnica de projeto, não um resultado de desempenho medido.

**Latência observada.** Nos testes reais informados no Windows, o `POST /processar_texto` levou **72.912 ms** na primeira requisição e **12.906 ms** na segunda, em um exemplo de **159 tokens de entrada e 45 de saída** na primeira geração. A primeira requisição incluiu carregamento do modelo; portanto, esses tempos **não devem ser comparados como se fossem medições equivalentes**. No experimento posterior com o documento Siconfi, os tempos registrados foram **54.426 ms (Básico), 16.244 ms (Estruturado) e 21.392 ms (Fundamentado)**, com 255, 267 e 384 tokens de saída, respectivamente. Esses dados demonstram execução real e variação de tempo; não demonstram que um prompt ou modelo seja sempre mais rápido. Os registros estão no [relatório de testes](documentacao/RESULTADOS_TESTES_IA_LOCAL.md) e no [JSON experimental](documentacao/experimentos/avaliacao_prompts_final.json).

**Licença, acesso e disponibilidade.** O repositório oficial do modelo no Hugging Face indica a licença **[Apache 2.0](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE)**, permitindo uso e distribuição nos termos dessa licença. A disponibilidade pública dos pesos facilita reproduzir a instalação e consultar o cartão do modelo. Por tamanho, os **pesos não são colocados no GitHub deste projeto**: `scripts/baixar_modelo.py` os baixa uma vez para `models/qwen3-4b-instruct-2507/`. Durante a inferência, o código usa `local_files_only=True` e define `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`, evitando chamadas ao Hugging Face. **Não foi registrado um teste com a conexão de Internet fisicamente desligada.** O modelo local não elimina a necessidade de Internet para a coleta ou atualização das fontes fiscais e documentais.

**Decisão.** O **Qwen3-4B-Instruct-2507 em NF4** foi uma escolha intermediária: oferece geração orientada por instruções e funcionamento local com a memória disponível, sem depender de cobrança por chamada. Os modelos menores considerados não atendiam tão diretamente ao conjunto de tarefas; os maiores aumentariam o custo computacional. A decisão se apoia na arquitetura e em **testes reais com o Qwen**, sem afirmar que foi comprovado ser superior a todas as alternativas.

Fontes técnicas: [cartão do Qwen no Hugging Face](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [licença Apache 2.0 do modelo](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE), [T5-small no Hugging Face](https://huggingface.co/google-t5/t5-small), [BERT oficial](https://github.com/google-research/bert), [quantização bitsandbytes](https://huggingface.co/docs/transformers/quantization/bitsandbytes).

## 7. Arquitetura, rotas e tratamento de erros

```text
Fontes Siconfi / ONU / CGU / páginas governamentais
     ↓ coleta e organização local
CSV, TXT, JSONL e manifestos
     ↓ consulta e cálculos Python
FastAPI (Pydantic, validações, respostas JSON)
     ↓ cliente HTTP local
Streamlit (filtros, gráficos, tabelas, assistente)
     ↔ Qwen em GPU local, sob demanda
```

A API carrega os pesos **somente na primeira geração**, atende a um pedido de geração por vez e, por padrão, roda em `127.0.0.1:8000` com **um worker**. Os contratos de entrada e saída estão definidos com **Pydantic** e aparecem em `http://127.0.0.1:8000/docs`. O retorno de cada falha contém identificador de requisição quando aplicável.

| Endpoints principais | Utilização |
|---|---|
| `GET /health` e `GET /ia/health` | Diagnóstico geral e do modelo, sem carregamento obrigatório. |
| `GET /despesas`, `POST /despesas`, `GET /estatisticas` | Rotas históricas da amostra e dos registros manuais. |
| `GET /conteudo-web` | Conteúdo coletado por scraping. |
| `GET /dados-oficiais`, `/dados-oficiais/status`, `/dados-oficiais/serie`, `/dados-oficiais/regioes` | Consulta fiscal, cobertura, série e regiões. |
| `POST /processar_texto` | Texto livre para resumo ou explicação. |
| `GET /ia/documentos`, `POST /ia/resumir_documento` | Catálogo e sumarização documental. |
| `POST /ia/sintese_fiscal` | Síntese textual de indicadores calculados em Python. |
| `POST /ia/perguntar_dados` | Perguntas sobre despesas oficiais **ou** ODS 16, Governança ESG e o próprio projeto; Qwen opcional e fontes declaradas. |

O tratamento de falhas distingue **422** (entrada inválida), **429** (outra geração em andamento), **503** (modelo, GPU ou fonte indisponíveis), **504** (tempo de geração excedido) e **500** (erro interno). A interrupção do prazo de geração é **cooperativa**, não um cancelamento instantâneo da GPU. O limite de tempo padrão da geração é **180 segundos**. A documentação detalhada está em [API](documentacao/API.md), [contratos de resposta](documentacao/CONTRATOS_RESPOSTAS_API.txt) e [tratamento de erros](documentacao/TRATAMENTO_ERROS_HTTP.txt).

## 8. Instalação e execução (Windows, PowerShell)

Requisitos da instalação testada: **Python 3.11**, **16 GB de RAM**, GPU NVIDIA com CUDA e **aproximadamente 8 GB de VRAM** para o Qwen configurado. Sem GPU/pesos, o projeto ainda disponibiliza as rotas e os gráficos que não exigem geração pelo modelo.

Na raiz do projeto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para utilizar o Qwen local, instale uma edição de **PyTorch/CUDA compatível com driver e ambiente** (a instalação informada utilizou PyTorch com CUDA 12.6), além das dependências específicas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-llm.txt
.\.venv\Scripts\python.exe scripts/diagnostico_gpu.py
.\.venv\Scripts\python.exe scripts/baixar_modelo.py
```

O download do modelo é necessário somente na **primeira instalação**; não repita o processo para aplicar as atualizações incrementais.

Em dois terminais na pasta do projeto:

**Terminal 1 — FastAPI**

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Terminal 2 — Streamlit**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Acesse **http://localhost:8501** e **http://127.0.0.1:8000/docs**. As variáveis de ambiente `TP3_API_URL`, `TP3_DATA_DIR`, `TP4_MODEL_DIR` e `TP4_LLM_MAX_SECONDS` são **nomes internos legados, preservados para compatibilidade** com instalações existentes; não aparecem em nomes de arquivos ou pastas. O [guia de instalação](documentacao/GUIA_LLM_LOCAL.md) traz os passos técnicos adicionais. Evite múltiplos workers com a mesma GPU.

Para repetir coletas, quando necessário:

```powershell
.\.venv\Scripts\python.exe coleta_web.py
.\.venv\Scripts\python.exe coleta_selenium.py
.\.venv\Scripts\python.exe preparar_llm.py
.\.venv\Scripts\python.exe scripts/coletar_siconfi.py --todas
```

Coletar novamente exige Internet e, no caso do Selenium, navegador e driver compatíveis. A base fiscal consolidada já está no projeto: **não é necessário repetir a coleta para abrir o dashboard**.

## 9. Testes e evidências

A versão atual do projeto foi novamente verificada com:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Resultado da versão atual: 259 testes automatizados aprovados, oito avisos de depreciação e nenhuma falha.** Os testes cobrem dados e paginação, Siconfi, estatísticas, navegação, contratos Pydantic, HTTP e erros, coleta Web, sumarização, prompts, perguntas fiscais e integração do dashboard. O serviço de IA é simulado nos testes automatizados para evitar carregar pesos e GPU. A verificação estrutural do CSV oficial confirmou cobertura completa de 405 combinações, sem duplicidades.

Além disso, **o autor informou que testou a aplicação completa em seu computador e não encontrou problemas**, incluindo os recursos em funcionamento no ambiente local. Essa é uma **validação manual informada pelo autor**, distinta da bateria automatizada e de uma avaliação formal com usuários externos. O Qwen também produziu resultados reais documentados nos testes HTTP e no experimento dos três prompts; os valores e durações foram preservados sem alterações.

Com a FastAPI aberta, podem ser executados testes complementares:

```powershell
.\.venv\Scripts\python.exe scripts/verificar_erros_http.py
.\.venv\Scripts\python.exe scripts/verificar_dashboard.py
.\.venv\Scripts\python.exe scripts/teste_perguntas_http_real.py
.\.venv\Scripts\python.exe scripts/teste_sumarizacao_http_real.py --fiscal
.\.venv\Scripts\python.exe scripts/avaliar_prompts.py
```

Os scripts de inferência precisam dos pesos e da GPU; os scripts de diagnóstico podem funcionar sem carregar o modelo. Os resultados históricos, as limitações e os testes estão registrados no [relatório geral](documentacao/RELATORIO_TESTES.md), nos [testes locais da IA](documentacao/RESULTADOS_TESTES_IA_LOCAL.md) e na [apresentação da solução](documentacao/APRESENTACAO_DA_SOLUCAO.md).

## 10. Limitações e cuidados metodológicos

- Os valores do Siconfi são declarações fiscais e não foram auditados independentemente pela aplicação; a análise não garante correção substancial de cada declaração.
- O **subtotal** mostrado no dashboard inclui somente as funções selecionadas; não deve ser chamado de orçamento total do estado. As porcentagens são relativas ao mesmo recorte.
- Não há população oficial anual integrada, despesa per capita, IPCA aplicado ou inferência sobre qualidade de serviços, eficiência e causalidade.
- O Qwen gera texto e pode produzir informações incorretas. Valores financeiros devem ser conferidos nos campos calculados em Python e nas fontes indicadas.
- O projeto não possui mecanismo RAG vetorial, memória conversacional persistente nem agente autônomo. O assistente usa os documentos selecionados e consultas fiscais controladas.
- O cadastro de despesas manuais não dispõe de autenticação. **Mantenha a API em `127.0.0.1`**; não exponha o serviço publicamente sem segurança adicional.
- A inferência é local após o download dos pesos; isso não significa que as etapas de coleta funcionem sem rede, nem que um teste totalmente desconectado já tenha sido realizado.

## 11. Estrutura de arquivos e documentação

```text
Transparencia_Brasil_/
├── app.py                        # Entrada Streamlit
├── pages/                        # Telas visíveis e código histórico preservado
├── api/                          # Rotas, contratos Pydantic e tratamento de erros
├── services/                     # Serviço Qwen, Siconfi, documentos e prompts
├── utils/                        # Cálculos, cliente HTTP e componentes visuais
├── scripts/                      # Coleta, diagnóstico, avaliação e verificação
├── data/
│   ├── siconfi/                  # Base oficial, manifesto e critérios
│   ├── llm/                      # Corpus preparado e manifesto
│   ├── conteudo_web.csv          # Três documentos institucionais
│   ├── conteudo_selenium.csv     # Um documento coletado por navegador
│   └── amostra_dados.csv         # Amostra ilustrativa para histórico e testes
├── tests/                        # Testes automatizados
├── documentacao/                 # Artefatos TDSP, manuais e resultados
├── requirements.txt
├── requirements-llm.txt
├── DECLARACAO_USO_IA.txt
└── README.md
```

Documentos principais:

| Material | Arquivo |
|---|---|
| Artefatos TDSP completos | [PDF](documentacao/TDSP_ARTEFATOS_REVISADOS.pdf) e [DOCX](documentacao/TDSP_ARTEFATOS_REVISADOS.docx) |
| Project Charter | [PROJECT_CHARTER.md](documentacao/PROJECT_CHARTER.md) |
| Data Summary Report | [DATA_SUMMARY_REPORT.md](documentacao/DATA_SUMMARY_REPORT.md) |
| Evolução desde a proposta original | [CONFRONTO_PROPOSTA_ORIGINAL.md](documentacao/CONFRONTO_PROPOSTA_ORIGINAL.md) |
| Modelo e instalação | [GUIA_LLM_LOCAL.md](documentacao/GUIA_LLM_LOCAL.md) |
| Engenharia de prompts | [SUMARIZACAO_COM_LLM.md](documentacao/SUMARIZACAO_COM_LLM.md) e [AVALIACAO_EXPERIMENTAL_PROMPTS.md](documentacao/AVALIACAO_EXPERIMENTAL_PROMPTS.md) |
| Resultado real dos prompts | [JSON](documentacao/experimentos/avaliacao_prompts_final.json) |
| Dashboard e consultas fiscais | [DASHBOARD_INTEGRADO.md](documentacao/DASHBOARD_INTEGRADO.md), [PERGUNTAS_DADOS_OFICIAIS.md](documentacao/PERGUNTAS_DADOS_OFICIAIS.md) |
| Testes e contratos | [RELATORIO_TESTES.md](documentacao/RELATORIO_TESTES.md), [API.md](documentacao/API.md) |
| Apresentação e argumentação | [PDF](documentacao/APRESENTACAO_DA_SOLUCAO.pdf), [DOCX](documentacao/APRESENTACAO_DA_SOLUCAO.docx) e [Markdown](documentacao/APRESENTACAO_DA_SOLUCAO.md) |

A versão do GitHub inclui código, documentação, manifesto e base fiscal consolidada, mas **não inclui** os pesos do Qwen (`models/`), o ambiente virtual (`.venv/`), caches brutos, backups e dados manuais privados. Para publicar pela interface do GitHub, **extraia o ZIP e envie os arquivos e pastas de dentro de `Transparencia_Brasil_/` à raiz do repositório**, incluindo `.gitignore`; enviar apenas o ZIP não publica a estrutura do projeto. **Se o repositório já contém arquivos antigos com nomes de etapas ou questões acadêmicas, é necessário excluí-los do GitHub além de enviar os novos**; o envio pelo navegador não apaga arquivos cujo nome foi alterado. Essa limpeza de nomes não altera a lógica da aplicação. As variáveis internas legadas de ambiente foram mantidas para compatibilidade.

O projeto teve uma evolução progressiva: amostra ilustrativa de três UFs; coleta Web e estrutura de dados; FastAPI com validações e tratamento de erros; Qwen local quantizado; base fiscal nacional; sumarização e consultas em linguagem natural; reorganização do dashboard; documentação TDSP e apresentação final. As decisões e os resultados estão registrados nos documentos acima, e o [uso de IA no desenvolvimento](DECLARACAO_USO_IA.txt) está declarado separadamente.

## 12. ODS 16 e Governança: explicação interativa pelo Qwen

**Esta é uma funcionalidade da própria aplicação, não um documento isolado de evidência.** Foi criada para que uma pessoa possa perguntar diretamente como o Transparência Brasil se relaciona com o **ODS 16 — Paz, Justiça e Instituições Eficazes** e com o eixo **Governança (G)** de ESG.

### Duas maneiras de perguntar

1. Em **Assistente IA → Perguntar aos dados**, digite, por exemplo, **“Como o Transparência Brasil contribui para o ODS 16?”**. A aplicação reconhece o assunto e muda do motor de cálculos fiscais para o contexto documental, sem prejudicar as perguntas de despesas.
2. Em **Assistente IA → ODS 16 e Governança**, utilize a **categoria exclusiva** com perguntas sugeridas sobre as metas **16.6** e **16.10**, acesso à informação, transparência e controle social, ou escreva sua própria pergunta.

### De onde vem a resposta

A FastAPI utiliza dois conjuntos de informações já existentes no projeto: (a) a página da **ONU Brasil sobre o ODS 16**, coletada em 19/10/2026 e preservada em `data/conteudo_web.csv`, da qual são extraídas as metas **16.6** e **16.10**; (b) fatos verificáveis sobre as funcionalidades, fontes e limitações do Transparência Brasil, em `data/ods16/contexto_projeto.json`, coerentes com este README.

O **Python seleciona e verifica essas informações**; o **Qwen3-4B-Instruct-2507** recebe o contexto e produz uma explicação em português com limite padrão de **384 tokens**. A interface mostra a explicação do modelo separadamente do resumo factual verificado, informa as fontes e destaca as limitações. Se o modelo estiver indisponível, o resumo factual e as fontes continuam acessíveis.

A ligação defendida é concreta: disponibilizar dados fiscais com filtros, gráficos e explicações facilita o **acesso público à informação (meta 16.10)** e o acompanhamento de despesas, tema associado à **transparência institucional (meta 16.6)** e à **Governança ESG**. **O projeto não mede resultados do ODS 16, não classifica a qualidade dos governos e não audita dados fiscais.**

### Teste da nova função

Com a FastAPI e o Streamlit executando, abra **Assistente IA → ODS 16 e Governança**, escolha **“Como o Transparência Brasil está relacionado ao ODS 16?”** e acione **“Explicar ODS 16 e Governança”**. Repita a mesma pergunta em **Perguntar aos dados**. As duas entradas usam o mesmo contexto e devem apresentar fontes da ONU e da documentação local. Para testar a classificação sem GPU:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A execução **real dessa nova explicação pelo Qwen** deverá ser validada na instalação local com os pesos e a GPU disponíveis; os testes automatizados simulam a geração e conferem os contratos sem atribuir respostas inventadas ao modelo. Consulte também [`documentacao/ODS16_E_GOVERNANCA_INTERATIVA.md`](documentacao/ODS16_E_GOVERNANCA_INTERATIVA.md).
