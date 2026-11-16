# Data Summary Report — Transparência Brasil

Este relatório apresenta os conjuntos de dados disponíveis, sua procedência e os cuidados necessários para interpretá-los. A aplicação mantém separados os registros ilustrativos, as coletas documentais e os dados fiscais declarados ao Siconfi.

## Visão geral

| Conjunto | Arquivo principal | Conteúdo nesta versão | Natureza |
|---|---|---|---|
| Amostra ilustrativa | `data/amostra_dados.csv` | 9 registros de 2025 para SP, GO e BA | Valores demonstrativos, não auditados |
| Conteúdo Beautiful Soup | `data/conteudo_web.csv` | 3 fontes institucionais | Textos Web com URL e método de coleta |
| Conteúdo Selenium | `data/conteudo_selenium.csv` | 1 fonte institucional | Texto de coleta por navegador |
| Preparação para LLM | `data/llm/documentos.jsonl` | 16 fragmentos, conforme manifesto | Textos preparados, sem inferência nessa etapa |
| Base Siconfi | `data/siconfi/despesas_oficiais.csv` | 405 registros declarados, 27 UFs, 2021–2025 | Dados oficiais declarados; não auditados pelo projeto |
| Cadastros manuais | `data/registros_manuais.csv` | Arquivo local, não publicado | Dados inseridos por usuário, sem comprovação externa |

## 1. Amostra inicial — três estados

O arquivo `amostra_dados.csv` inclui Educação, Saúde e Segurança Pública para São Paulo, Goiás e Bahia no ano de 2025. Também apresenta população e rótulos de fontes Siconfi/IBGE, mas não contém os identificadores de extração necessários para conferir cada número. Por essa razão, todos os resultados de **Gastos públicos** e **Estatísticas** derivados desse arquivo são identificados como **ilustrativos**.

A página Estatísticas calcula composição das três funções, valores por habitante, rankings, comparações entre dois estados, perfil estadual, matrizes, média, mediana, mínimo, máximo e amplitude. A participação percentual de cada função é calculada sobre **a soma das três funções da amostra**, não sobre o orçamento completo do estado.

O cadastro manual via API escreve em arquivo diferente e não modifica os nove registros originais.

## 2. Textos institucionais coletados da Web

`coleta_web.py` utiliza Requests e Beautiful Soup nas páginas do ODS 16 (ONU Brasil), do Siconfi (Tesouro Nacional) e da transparência pública (CGU). O CSV registra os métodos e as datas de coleta. O script preserva informações anteriores quando uma consulta falha, em vez de atribuir sucesso a uma operação não executada.

`coleta_selenium.py` realiza a aquisição de texto da página governamental sobre informações obrigatórias de transparência ativa. Os arquivos CSV e TXT fornecidos registram uma coleta efetiva por `selenium+chromium`. Os testes automatizados do coletor utilizam navegador simulado e não constituem uma nova consulta ao portal.

O endpoint `GET /conteudo-web` reúne os três registros Beautiful Soup e o registro Selenium, quando os arquivos estão presentes.

## 3. Corpus preparado para IA

O arquivo `data/llm/manifesto.json` registra **16 fragmentos**: sete fragmentos de quatro fontes Web e nove descrições dos dados ilustrativos. Parte dos textos é fracionada, de modo que o número de fragmentos Web não corresponde ao número de páginas.

Essa preparação não executa o Qwen. A inferência local ocorre posteriormente, por meio da API FastAPI e do serviço `services/llm_service.py`. O conteúdo JSONL não está conectado a uma busca RAG automática nesta versão.

## 4. Base oficial declarada ao Siconfi

A coleta local gerou `data/siconfi/despesas_oficiais.csv` e `data/siconfi/manifesto.json`. O manifesto presente nesta versão informa **135 combinações UF/ano válidas, 405 registros padronizados e nenhuma combinação pendente**. A verificação deste pacote confirmou a presença das 27 UFs, dos cinco exercícios e das três funções, sem duplicidade no identificador UF/ano/função.

Critérios utilizados:

- Fonte: API do Siconfi, RREO, Anexo 02;
- Exercícios: 2021, 2022, 2023, 2024 e 2025;
- Período: 6º bimestre de cada ano;
- Estágio: despesas liquidadas **acumuladas até o bimestre (d)**;
- Funções: Segurança Pública (06), Saúde (10) e Educação (12);
- Abrangência: despesas exceto intraorçamentárias;
- Valor: em reais nominais, com URL da consulta, data de coleta e hash da fonte.

A origem é uma declaração oficial do ente, mas **a validação automática do programa não substitui a conferência contábil independente**. O cache bruto em `data/siconfi/raw/` e os históricos locais não fazem parte dos arquivos destinados à publicação no GitHub. Os valores consolidados, o manifesto, o coletor e a documentação acompanham a entrega.

Os valores representam **despesas dos governos estaduais e do Distrito Federal**, não necessariamente todas as despesas públicas realizadas no território das UFs. O Distrito Federal acumula competências estaduais e municipais. Não há dados de população oficial integrados por exercício, nem correção pela inflação nessa base.

## 5. Regras de qualidade e limites

As validações verificam tipos, estrutura, períodos, classificação, duplicatas, ausência de dados e coerência interna de valores conforme as regras programadas. Para a leitura pública, devem permanecer claros os limites de cada base:

- Valores ilustrativos não podem ser anunciados como despesas públicas verificadas.
- As três funções selecionadas no Siconfi não formam o orçamento total de cada governo.
- Despesas maiores não comprovam melhor desempenho da gestão.
- Variações anuais na base Siconfi são nominais, sem ajuste inflacionário.
- Dados coletados não equivalem a dados auditados pela aplicação.

Para reproduzir a coleta e acompanhar eventuais retificações, consulte [`DADOS_OFICIAIS_SICONFI.md`](DADOS_OFICIAIS_SICONFI.md). Para detalhes da IA, consulte [`GUIA_LLM_LOCAL.md`](GUIA_LLM_LOCAL.md).
