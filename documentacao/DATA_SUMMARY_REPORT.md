# Data Summary Report — Transparência Brasil (atualizado em novembro de 2026)

## 1. Objetivo deste relatório

Este relatório apresenta as bases de dados e os textos usados na aplicação, como foram coletados, quais tratamentos receberam e onde aparecem no dashboard. A primeira versão previa principalmente informações de São Paulo, Goiás e Bahia, combinando Siconfi e população do IBGE. O projeto acabou sendo ampliado e hoje utiliza uma base fiscal de 27 UFs. Os números ilustrativos e os dados oficiais são mantidos separados.

## 2. Conjuntos de dados disponíveis

| Conjunto | Arquivo principal | Cobertura e finalidade |
|---|---|---|
| Siconfi / RREO | `data/siconfi/despesas_oficiais.csv` | 405 registros; 27 UFs; 2021 a 2025; três funções. Base dos gráficos e das consultas fiscais. |
| Manifesto fiscal | `data/siconfi/manifesto.json` | Descreve a coleta, 135 combinações UF/ano válidas e zero pendências. |
| Textos Beautiful Soup | `data/conteudo_web.csv` | Três páginas institucionais: ONU Brasil, Siconfi/Tesouro Nacional e CGU. |
| Texto Selenium | `data/conteudo_selenium.csv` | Uma página governamental sobre transparência ativa, coletada com `selenium+chromium`. |
| Preparação LLM | `data/llm/documentos.jsonl` | 16 fragmentos: sete trechos Web e nove descrições da amostra ilustrativa. |
| Amostra inicial | `data/amostra_dados.csv` | Nove registros ilustrativos de SP, GO e BA em 2025, preservados só para histórico e testes. |

## 3. Aquisição dos dados fiscais

A coleta fiscal foi feita com `scripts/coletar_siconfi.py`, que utiliza a API de Dados Abertos do Siconfi. O programa foi configurado para extrair **RREO, Anexo 02**, sempre o **sexto bimestre** dos exercícios de **2021 a 2025**, na coluna **DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)**. Foram escolhidas as linhas gerais das funções **06 — Segurança Pública**, **10 — Saúde** e **12 — Educação**, excluindo despesas intraorçamentárias.

A extração foi padronizada por UF, ano e função. Cada registro informa, entre outros campos, `uf`, `estado`, `ano`, `funcao`, `codigo_funcao`, `valor_reais`, `estagio`, `periodo`, `abrangencia`, `fonte_url`, `data_coleta_utc` e `hash_fonte_sha256`. O manifesto salva os critérios da seleção e a cobertura. Os arquivos brutos em cache não acompanham o ZIP de publicação, mas o CSV consolidado, o manifesto e o código da coleta acompanham.

Nesta revisão, o CSV contém **405 linhas** (27 × 5 × 3). A estrutura foi conferida quanto à quantidade de linhas, aos exercícios, às funções e à presença das UFs. Isso é uma validação **estrutural**, não uma auditoria dos demonstrativos fiscais. Os valores representam declarações dos governos estaduais e do Distrito Federal ao Siconfi, e não todo o gasto público realizado no território de cada UF.

## 4. Coleta de textos institucionais

O arquivo `coleta_web.py` usa **Requests e Beautiful Soup** para ler páginas de três instituições: ONU Brasil (ODS 16), Tesouro Nacional (API do Siconfi) e CGU (transparência pública). Os registros guardam título, URL, texto, data e método de coleta. Os documentos foram reunidos em `data/conteudo_web.csv` e TXT.

O arquivo `coleta_selenium.py` utiliza um navegador automatizado. O material armazenado registra uma execução real em **19/10/2026** na página de informações obrigatórias de transparência ativa, com método `selenium+chromium`. Os testes automatizados desse coletor usam um navegador simulado; por isso, não representam nova coleta real.

Os textos institucionais são usados para explicar o contexto da transparência pública e para que o usuário possa solicitar resumos. Eles não são a fonte dos valores fiscais que aparecem nos gráficos.

## 5. Tratamento e preparação

Para o painel fiscal, os scripts organizam e conferem as combinações UF/ano/função. O programa calcula rankings, diferenças, evolução histórica e estatísticas descritivas em Python. Se faltar algum valor, a ausência é sinalizada; não deve ser tratada como zero.

Para os textos, `preparar_llm.py` gera um corpus em JSONL com **16 fragmentos**, segundo o manifesto. Essa preparação organiza os documentos, mas **não executa o Qwen automaticamente**. A sumarização acontece depois, quando a aplicação recupera um documento selecionado e o envia ao modelo local. Conteúdos longos podem ser divididos em trechos para sumarização por etapas.

## 6. Integração com a aplicação e com a IA

O fluxo implementado é: **coleta → arquivos e manifestos → tratamento em Python → FastAPI → Streamlit → explicação ou resumo com Qwen, quando solicitado**.

A página **Gastos públicos** consulta a base do Siconfi via API para mostrar gráficos, rankings, filtros e comparações. O Python calcula os números; o Qwen recebe os resultados já calculados para produzir uma explicação em linguagem natural. Em **Assistente IA**, o usuário também pode perguntar sobre as despesas ou resumir documentos institucionais. O projeto não utiliza o Qwen para criar os números das despesas.

A engenharia de prompts foi avaliada com as versões **Básico**, **Estruturado** e **Fundamentado**. O experimento real usou um texto coletado sobre a API do Siconfi e limite de 384 tokens, com resultados guardados em `documentacao/experimentos/avaliacao_prompts_final.json`. Os dois primeiros resumos terminaram; o terceiro foi interrompido no limite. Como foi uma execução por versão e um documento, o resultado não permite conclusões gerais sobre qual prompt é melhor em qualquer situação.

## 7. Limitações identificadas

- O dashboard soma as despesas das funções selecionadas para cada UF e exercício; esse subtotal **não corresponde ao total de todas as funções governamentais**.
- As porcentagens mostram a participação de cada função **no subtotal das três funções**, não no orçamento inteiro.
- Ainda não foi integrada uma série oficial de população do IBGE; **não há despesa por habitante na base atual**.
- Os valores são nominais, sem atualização pelo IPCA.
- A conferência da estrutura não substitui o confronto amostral dos números com o demonstrativo original.
- Os dados ilustrativos de 2025 continuam no repositório para histórico e testes, mas não são utilizados no dashboard oficial.
- O Qwen pode errar; as fontes e os resultados fiscais calculados devem permanecer disponíveis para conferência.

## 8. Resumo

O projeto passou de uma amostra ilustrativa de três estados para uma base fiscal nacional. Também reuniu documentos coletados com duas técnicas de Web scraping e passou a utilizar um modelo de linguagem local para produzir explicações. Dessa forma, foi possível demonstrar o ciclo de Ciência de Dados desde a coleta e o tratamento até a apresentação de gráficos e resumos. As limitações acima continuam registradas porque são importantes para a interpretação correta dos resultados.

**Documento completo:** [`TDSP_ARTEFATOS_REVISADOS.pdf`](TDSP_ARTEFATOS_REVISADOS.pdf).
