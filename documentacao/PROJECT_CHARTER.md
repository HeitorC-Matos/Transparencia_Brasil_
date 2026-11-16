# Project Charter — Transparência Brasil

## Propósito

O Transparência Brasil foi criado para aproximar o cidadão das informações sobre despesas públicas. O projeto reúne visualizações, consultas por API e explicações em linguagem natural para reduzir as barreiras de interpretação dos dados. Está relacionado ao ODS 16, especialmente à transparência e ao acesso público à informação.

A aplicação foi iniciada com uma **amostra ilustrativa de São Paulo, Goiás e Bahia, referente a 2025**. Posteriormente ganhou uma base independente de despesas declaradas ao Siconfi para **as 27 unidades da Federação, de 2021 a 2025**. As duas origens permanecem separadas.

## Público-alvo

Cidadãos interessados em transparência pública; como públicos secundários, estudantes, pesquisadores, jornalistas e organizações sociais. A interface busca explicar os indicadores sem exigir formação prévia em contabilidade governamental.

## Objetivos

- Apresentar os registros ilustrativos com filtros, gráficos e estatísticas descritivas, sem atribuir caráter oficial a seus valores.
- Consultar dados de despesas liquidadas declaradas ao Siconfi, com critérios de seleção verificáveis e identificação da fonte.
- Permitir comparações entre unidades da Federação e exercícios, respeitando os limites de comparabilidade.
- Disponibilizar uma API FastAPI com contratos de entrada e saída validados e mensagens claras quando ocorrerem falhas.
- Oferecer resumos e explicações de textos por meio do Qwen executado localmente.
- Preservar os dados originais, automatizar testes e documentar as escolhas metodológicas.

## Funcionalidades disponíveis

| Componente | Implementação |
|---|---|
| Interface | Streamlit, com sete seções: App, Gastos públicos, Estatísticas, Dados oficiais, Conteúdo da Web, API FastAPI e Assistente IA. |
| Amostra | Nove registros de 2025, três estados e três funções, com estatísticas comparativas e per capita ilustrativas. |
| Dados oficiais | Base consolidada Siconfi com 405 registros em 27 UFs e cinco exercícios, segundo o manifesto da coleta. |
| API | FastAPI com consultas, registro manual separado, `response_model` e tratamento de erros. |
| Conteúdo documental | Textos institucionais coletados por Beautiful Soup e Selenium. |
| IA local | Qwen3-4B-Instruct-2507 para resumos e explicações, carregado em disco com Transformers/PyTorch. |
| Qualidade | Testes unitários e de integração automatizados, além de testes reais de geração informados pelo usuário. |

## Decisões metodológicas

A amostra ilustrativa permanece imutável e não é misturada à base do Siconfi. Nos dados oficiais, utiliza-se o RREO, Anexo 02, 6º bimestre, com **despesas liquidadas acumuladas** das funções Educação (12), Saúde (10) e Segurança Pública (06), excluídas as intraorçamentárias. As agregações regionais exigem cobertura completa; o programa não converte ausências em zero.

O Siconfi é uma fonte de dados declarados pelos entes, mas a coleta e as regras automatizadas **não certificam a correção contábil dos valores**. A aplicação também não permite inferir qualidade da gestão somente pelo volume de despesas.

O modelo de IA opera localmente após o download dos pesos. As entradas e saídas são validadas com Pydantic; falhas de carregamento, limite de concorrência e timeouts recebem respostas HTTP específicas. O modelo **não consulta autonomamente todo o corpus documental**, nem substitui os cálculos realizados em Python.

## Riscos e controles

| Risco | Controle adotado |
|---|---|
| Confundir valores ilustrativos com oficiais | Bases independentes, identificação de origem e avisos visíveis. |
| Divergência ou retificação em demonstrativos | Armazenamento local da origem e manifesto, scripts de recolhimento e conferência amostral recomendada. |
| Comparações indevidas entre UFs | Mesmos critérios de ano, estágio e função; ressalva sobre diferenças institucionais do DF. |
| Interrupção de fontes externas | Cache de coleta, sinalização de falhas e preservação de resultados anteriores quando aplicável. |
| Indisponibilidade do Qwen | Diagnóstico específico, erros HTTP e independência das consultas fiscais. |
| Respostas incorretas da IA | Avisos de verificação, validação estrutural e apresentação das fontes dos valores selecionados. |
| Exposição indevida da API de cadastro | Uso local, sem publicação aberta e sem autenticação presumida. |

## Evoluções previstas

Aprimorar a conferência documental da coleta nacional; incorporar despesas totais comparáveis e denominadores oficiais; relacionar população do IBGE por exercício; permitir indicadores per capita oficiais e correção monetária; avaliar a fidelidade das explicações geradas pelo Qwen; e ampliar gradualmente o mecanismo de recuperação documental.

Essas evoluções **não são funcionalidades concluídas nesta versão**.
