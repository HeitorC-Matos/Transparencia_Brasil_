# Project Charter — Transparência Brasil (atualizado em novembro de 2026)

## 1. Por que o projeto existe

Os portais públicos divulgam informações sobre despesas, mas nem sempre é simples para o cidadão encontrar e entender esses dados. O Transparência Brasil foi criado para apresentar parte dessas informações em gráficos e tabelas mais acessíveis, além de permitir perguntas e explicações em linguagem natural. O projeto não pretende classificar estados como mais eficientes apenas porque gastaram menos.

## 2. Objetivo, público e relação com o ODS

O objetivo geral é facilitar a consulta e a comparação de informações sobre despesas públicas estaduais, usando Python, dados abertos e inteligência artificial local. O principal público é o cidadão comum; estudantes, jornalistas e pesquisadores também podem utilizar o sistema. O trabalho está relacionado ao pilar **Governança** do ESG e ao **ODS 16**, especialmente às metas **16.6** (instituições responsáveis e transparentes) e **16.10** (acesso à informação).

## 3. Escopo que foi implementado

- A proposta original previa três estados (São Paulo, Goiás e Bahia), despesas totais, proporções no orçamento e despesas por habitante, com uso principal dos dados anuais do DCA e população do IBGE.
- A versão atual trabalha com **26 estados e o Distrito Federal**, exercícios **2021 a 2025**, e três funções: **Educação, Saúde e Segurança Pública**.
- O indicador fiscal utilizado é **despesa liquidada acumulada até o sexto bimestre**, extraído do **RREO, Anexo 02, do Siconfi**, sem os registros intraorçamentários.
- A base consolidada incluída no projeto tem **405 registros** (27 UFs × 5 exercícios × 3 funções), sem pendências no manifesto da coleta.
- A página Gastos públicos exibe o **total das despesas das funções selecionadas** para cada UF e exercício. A participação percentual se refere a esse recorte e não ao orçamento inteiro do estado. A série de população do IBGE ainda não foi integrada à base oficial. Assim, **não existe per capita oficial** nesta versão.

## 4. Recursos entregues

| Recurso | Situação |
|---|---|
| Coleta fiscal pela API do Siconfi | Implementada e documentada. |
| Coleta de páginas institucionais por Beautiful Soup e Selenium | Implementada; quatro documentos armazenados. |
| Dashboard Streamlit | Implementado na página **Gastos públicos**, com filtros e estatísticas nacionais. |
| API FastAPI | Implementada, com rotas, validações e tratamento de erros. |
| IA local | Qwen3-4B-Instruct-2507 para sumarização documental, explicações e perguntas fiscais. |
| Engenharia de prompts | Três versões testadas; experimento real em JSON disponível. |
| Testes | 259 testes automatizados aprovados na versão conferida; 8 avisos. |

A página **App** apresenta o projeto; **Gastos públicos** concentra gráficos e insights; **Dados oficiais** reúne a consulta aos registros; **Conteúdo da Web** guarda os textos; **API FastAPI** descreve os serviços; e **Assistente IA** recebe perguntas e pedidos de resumo.

## 5. Fontes e tecnologias

- Fontes fiscais: API do Siconfi/Tesouro Nacional, RREO, Anexo 02.
- Fontes textuais: ONU Brasil (ODS 16), Tesouro Nacional, CGU e página governamental de transparência ativa.
- Tecnologias: Python, Streamlit, FastAPI, Requests, Beautiful Soup, Selenium, Pandas, Pydantic e Qwen executado localmente.
- Organização: cinco fases do **Team Data Science Process (TDSP)**.

## 6. Riscos, cuidados e metas de aceitação

Os valores fiscais são declarações ao Siconfi; o sistema não realiza auditoria independente dos demonstrativos. A amostra inicial de nove registros é **ilustrativa** e permanece separada da base oficial. Nos cálculos, dados ausentes não devem ser transformados em zero. As respostas do Qwen podem ter erros; os valores e fontes devem ser conferidos na aplicação.

A aceitação técnica foi verificada com **259 testes automatizados** e o autor informou ter executado a aplicação completa em seu computador sem encontrar problemas. Isso não substitui a conferência amostral dos valores diretamente nos demonstrativos. Como evoluções possíveis, ficam a integração do IBGE, a ampliação do escopo de funções e novas avaliações dos prompts.

## 7. Entregas e evidências

O trabalho mantém o código e os dados consolidados no repositório, com os relatórios de coleta e os resultados do experimento de IA em `documentacao/`. O documento completo revisado é [`TDSP_ARTEFATOS_REVISADOS.pdf`](TDSP_ARTEFATOS_REVISADOS.pdf), acompanhado da versão editável `.docx`. O PDF original foi guardado em `documentacao/historico/`, para comparação.
