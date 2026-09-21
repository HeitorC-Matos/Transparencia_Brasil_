# Data Summary Report - Transparência Brasil

## Objetivo dos dados

Os dados são utilizados para apresentar informações públicas de maneira simples na aplicação Streamlit e permitir comparações básicas entre estados e funções de despesa.

## Fonte 1 - Base de gastos públicos do TP1

Arquivo: `data/amostra_dados.csv`

A base utilizada no TP1 foi mantida no TP2 para preservar a continuidade do projeto. Ela contém registros de São Paulo, Goiás e Bahia.

### Campos principais

- `estado`: nome do estado;
- `sigla`: sigla da unidade da federação;
- `ano`: ano de referência;
- `funcao`: função da despesa;
- `valor_despesa`: valor utilizado na comparação;
- `populacao`: população de referência;
- `fonte_fiscal`: indicação da fonte fiscal;
- `fonte_populacao`: indicação da fonte populacional.

## Fonte 2 - Conteúdo da Web

Arquivos: `data/conteudo_web.csv` e `data/conteudo_web.txt`

O conteúdo é coletado pelo script `coleta_web.py` com as bibliotecas Requests e Beautiful Soup.

Páginas utilizadas:

- ODS 16 - Nações Unidas no Brasil;
- Siconfi - API de Dados Abertos do Tesouro Nacional.

### Campos do CSV da Web

- `titulo`: título da página;
- `url`: endereço consultado;
- `texto`: parte textual extraída da página.

## Uso na aplicação

A base do TP1 alimenta os filtros, a tabela e o gráfico de gastos públicos. O conteúdo extraído da Web alimenta uma tabela, a contagem de palavras e a nuvem de palavras.

## Qualidade e limitações

A base fiscal é uma amostra utilizada para fins acadêmicos e demonstração da aplicação. O conteúdo Web pode mudar conforme as páginas de origem forem atualizadas. Por isso, o script de coleta pode ser executado novamente para atualizar os arquivos CSV/TXT.
