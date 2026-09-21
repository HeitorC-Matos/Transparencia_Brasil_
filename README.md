# Transparência Brasil - TP2

Este projeto é a continuação direta do **TP1**. O tema, o problema e a base principal foram mantidos. No TP2 foram acrescentadas somente as funcionalidades solicitadas no enunciado.

## Repositório do projeto

Repositório GitHub criado para o projeto:

https://github.com/HeitorC-Matos/Transparencia_Brasil_

## O que foi acrescentado no TP2

- interface Streamlit com mais interação;
- extração de conteúdo da Web com Beautiful Soup;
- armazenamento do conteúdo em CSV e TXT;
- tabela, estatística de palavras e nuvem de palavras;
- uso de `st.cache_data`;
- uso de `st.session_state`;
- upload de CSV para complementar a base durante a sessão;
- download de CSV;
- controle de versão com Git e preparação para deploy;
- Project Charter e Data Summary Report finalizados.

## Estrutura do projeto

```text
Transparencia_Brasil_/
├── app.py
├── coleta_web.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── amostra_dados.csv
│   ├── conteudo_web.csv
│   └── conteudo_web.txt
└── documentacao/
    ├── PROJECT_CHARTER.md
    └── DATA_SUMMARY_REPORT.md
```

## Organização do projeto

O projeto segue o TDSP de maneira simples:

- **compreensão do negócio:** Project Charter;
- **aquisição e compreensão dos dados:** CSV do TP1, coleta Web e Data Summary Report;
- **desenvolvimento:** `app.py` e `coleta_web.py`;
- **implantação:** Git/GitHub e preparação para execução no Streamlit.

## 1. Criar o ambiente virtual

No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar as bibliotecas

```bash
pip install -r requirements.txt
```

## 3. Executar a coleta Web

```bash
python coleta_web.py
```

Esse comando atualiza os arquivos:

- `data/conteudo_web.csv`;
- `data/conteudo_web.txt`.

## 4. Executar a aplicação

```bash
streamlit run app.py
```

## 5. Git e GitHub

O repositório remoto já foi criado no GitHub. Para enviar os arquivos desta pasta ao repositório, executar no terminal:

```bash
git init
git add .
git commit -m "TP2 - Transparencia Brasil"
git branch -M main
git remote add origin https://github.com/HeitorC-Matos/Transparencia_Brasil_.git
git push -u origin main
```

O arquivo `.gitignore` evita o versionamento do ambiente virtual e de arquivos temporários do Python.

## 6. Preparação para deploy

O projeto está preparado para deploy no Streamlit porque possui:

- `app.py` como arquivo principal da aplicação;
- `requirements.txt` com as bibliotecas necessárias;
- arquivos de dados utilizados pela aplicação dentro da pasta `data/`;
- código versionável no repositório GitHub.

No Streamlit Community Cloud, após o projeto estar no GitHub, o arquivo principal a selecionar é:

```text
app.py
```

## Relação entre TP1 e TP2

No TP1 foi criada a aplicação inicial para comparar gastos públicos de São Paulo, Goiás e Bahia. No TP2 essa mesma aplicação foi mantida e recebeu apenas os recursos técnicos pedidos na segunda etapa, sem alterar o objetivo original do projeto.
