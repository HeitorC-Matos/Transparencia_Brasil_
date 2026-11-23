# Dados oficiais declarados ao Siconfi — metodologia e operação

## 1. Fonte e escopo

- Fonte: API de Dados Abertos do Siconfi / Secretaria do Tesouro Nacional.
- Endpoint: `GET /rreo` — `https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/rreo`.
- Relatório: RREO, **Anexo 02 — Despesas por Função/Subfunção**.
- Período de referência: **6º bimestre de cada exercício (2021 a 2025)**.
- Estágio da execução: **DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)**, acumuladas.
- Quadro: `cod_conta=RREO2TotalDespesas` (despesas exceto intraorçamentárias).
- Linhas sintéticas selecionadas: **Segurança Pública (06)**, **Saúde (10)** e **Educação (12)**.
- Entes: 26 governos estaduais e o governo distrital, identificados por `id_ente` (código IBGE da UF).
- Valores: nominais declarados à STN; **não auditados por esta aplicação**.
- **Limite de requisições:** no máximo uma por segundo, com intervalo mínimo configurado em 1,1 s.

Fontes oficiais para conferir os critérios:

- [Documentação da API Siconfi](https://apidatalake.tesouro.gov.br/docs/siconfi/)
- [Orientações do RREO e Anexo 2](https://siconfi.tesouro.gov.br/siconfi/pages/public/arquivo/conteudo/2024_Regras_Gerais_e_Instrucoes_de_preenchimento_RREO.pdf)
- [Tesouro Transparente — Metadados do RREO](https://www.tesourotransparente.gov.br/ckan/dataset/b74a4483-54f5-4625-8d23-e65515b075ef/resource/a387c7ae-6993-4710-9054-9e9be549b66d/download/Metadadosrreo.pdf)

## 2. Como executar a coleta

Abra o PowerShell **na raiz do projeto**. Ative o mesmo ambiente virtual que já utiliza a FastAPI e o Qwen.

### Fase A — piloto com três estados

```powershell
python scripts/coletar_siconfi.py --ufs SP GO BA
```

O comando consulta 2021, 2022, 2023, 2024 e 2025, totalizando 15 combinações UF/ano. Cada combinação válida deverá produzir exatamente três linhas (45 registros para uma coleta totalmente completa). O comando conserva as respostas originais em `data/siconfi/raw/UF/ANO.json` para conferência e reutilização.

**Atenção:** uma coleta parcial não pode ser apresentada como completa. Quando ocorrerem erros ou ausências, o comando retorna código de saída 2 e registra as pendências detalhadas em `data/siconfi/manifesto.json`.

Verifique em especial três valores no Siconfi, comparando manualmente os registros das funções com os valores que aparecem em `data/siconfi/despesas_oficiais.csv`. Uma validação manual independente é necessária antes de divulgar conclusões com dados reais.

### Fase B — 27 unidades federativas

Após verificar o piloto, execute:

```powershell
python scripts/coletar_siconfi.py --todas
```

O comando consulta 27 unidades e cinco exercícios (135 combinações; **405 registros** de função em caso de completude). Reutiliza as respostas previamente salvas e busca os anos/entes que faltarem. Se o servidor estiver instável, você pode executar novamente o mesmo comando, sem desperdiçar os downloads armazenados.

Para forçar atualização das declarações — por exemplo, após possíveis retificações:

```powershell
python scripts/coletar_siconfi.py --todas --atualizar
```

Reprocessamento local dos JSONs já coletados (sem internet):

```powershell
python scripts/coletar_siconfi.py --todas --somente-cache
```

### Fase C — FastAPI e Streamlit

**Terminal 1:**

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Terminal 2:**

```powershell
python -m streamlit run app.py
```

Na API, consulte `http://127.0.0.1:8000/docs`, em particular:

- `GET /dados-oficiais/status` — cobertura e pendências.
- `GET /dados-oficiais?uf=GO&ano=2025&funcao=Saúde` — seleção pontual.
- `GET /dados-oficiais/serie?uf=SP&funcao=Educação` — valores e variação nominal anual.
- `GET /dados-oficiais/regioes?ano=2025&funcao=Saúde` — agregados por grande região, somente com cobertura completa de todas as UFs da região.

No Streamlit, abra **Dados Oficiais — Siconfi**. A página permite selecionar ano, função e UF, examinar gráfico, tabela, link da fonte, baixar CSV, ver série anual e regional e solicitar explicação ao Qwen. A geração pelo Qwen requer o servidor FastAPI com modelo local instalado; a visualização dos dados funciona sem o modelo carregado.

## 3. Regras de consistência

O programa:

1. Busca somente as linhas sintéticas de função; **não soma subfunções nem todos os registros do demonstrativo**.
2. Usa apenas a coluna acumulada de despesa **liquidada**, não mistura empenhadas, pagas, percentuais nem valores no bimestre.
3. Exclui linhas do quadro intraorçamentário para não duplicar valores com a consolidação.
4. Confere UF, código do ente, exercício, bimestre, demonstrativo e anexo.
5. Exige exatamente uma linha para cada função selecionada e uma linha total do quadro não intraorçamentário.
6. Compara a soma das três funções selecionadas ao total não intraorçamentário do quadro, rejeitando somas superiores.
7. Rejeita números não finitos, valores negativos, duplicidades e campos essenciais ausentes.
8. Marca combinações UF/ano incompletas como pendentes, sem substituí-las por zero.
9. Salva a URL original, carimbo UTC e hash SHA-256 do JSON bruto usado na apuração.
10. Não mistura a base Siconfi com a amostra ilustrativa nem com cadastros manuais.

## 4. Escopo interpretativo e limitações

As despesas do governo estadual de SP não abrangem automaticamente o total das despesas dos seus municípios; o mesmo vale para as outras UFs. O DF acumula competências estaduais e municipais. Essas diferenças institucionais exigem cautela nas comparações.

As variações exibidas são **nominais**: não descontam inflação. Também não se comparam gastos por habitante sem uma série populacional IBGE aprovada e vinculada a cada ano. Indicadores per capita e variações reais não foram ativados nesta versão para evitar índices sem fontes verificadas. Despesa maior não comprova, por si só, melhora de políticas, qualidade da despesa ou eficiência.

O Siconfi reúne dados declarados pelos entes. A integração automática **não equivale à certificação contábil nem substitui a conferência dos demonstrativos oficiais**.

## 5. Evidências e controle de qualidade

- Arquivos brutos: `data/siconfi/raw/UF/ANO.json` (cache local, não publicar no Git).
- Versões anteriores de snapshots: `data/siconfi/historico/` (cópias de segurança locais, fora do Git).
- Base padronizada: `data/siconfi/despesas_oficiais.csv`.
- Cobertura e pendências: `data/siconfi/manifesto.json`.
- Testes sem rede: `python -m pytest -q`.

**A coleta real foi executada no computador do usuário, e a base consolidada foi incluída nesta entrega.** O `manifesto.json` atual registra 405 registros, 135 combinações UF/ano válidas e nenhuma pendência. A estrutura do CSV foi conferida quanto a combinações e duplicidades, mas ainda é recomendável comparar uma amostra de valores diretamente com as declarações oficiais. Os testes automáticos utilizam respostas sintéticas para validar regras e não se apresentam como coleta real. Não é necessário executar nova coleta apenas para abrir os gráficos; o script continua disponível para atualização e reprocessamento.

## 6. Proteção do trabalho anterior

As rotas `/despesas` e `/estatisticas` continuam utilizando apenas a amostra ilustrativa e os cadastros manuais. A nova base é disponibilizada exclusivamente pelas rotas `/dados-oficiais`. Os diretórios `models/`, `.venv/` e `.venv_tp4/` permanecem inalterados.
