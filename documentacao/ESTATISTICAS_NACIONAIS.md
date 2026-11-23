# Estatísticas nacionais — critérios e funcionamento

A página **Gastos públicos** utiliza a base fiscal coletada no Siconfi para permitir que o usuário escolha uma, várias ou todas as 27 unidades da Federação e analise os exercícios de 2021 a 2025. A seleção inicial é nacional. A página antiga de valores ilustrativos de São Paulo, Goiás e Bahia foi retirada do menu, mas seu código, a amostra e os testes históricos foram preservados.

## Origem e padrão dos registros

Os dados são consultados pela FastAPI nas rotas `GET /dados-oficiais` e `GET /dados-oficiais/status`. A base versionada em `data/siconfi/despesas_oficiais.csv` contém despesas **liquidadas acumuladas até o 6º bimestre**, provenientes do **RREO — Anexo 02**, somente nas funções **Educação (12), Saúde (10)** e **Segurança Pública (06)**, no quadro de despesas não intraorçamentárias. Foram extraídos registros dos governos estaduais e distrital, não de seus municípios.

O arquivo `data/siconfi/manifesto.json` registra a cobertura e as pendências da última coleta. A extração está documentada em `documentacao/DADOS_OFICIAIS_SICONFI.md`. A aplicação apresenta as declarações oficiais, mas **não realizou auditoria independente dos valores**.

## Indicadores e regras

- **Recorte nacional:** a tela inicia com todas as 27 UFs selecionadas. Os filtros comuns de UFs, exercício e funções afetam simultaneamente os gráficos, as análises detalhadas e o contexto da explicação pelo Qwen. É possível escolher uma ou várias UFs.
- **Soma das funções:** agrega apenas funções escolhidas e **somente UFs que contenham todos os registros dessas funções** no exercício. Se faltar algum registro, a UF não integra o total/ranking e a pendência é informada; falta não vira zero.
- **Composição percentual:** despesa da função dividida pela soma das três funções da mesma UF e ano, multiplicada por 100. Esta proporção **não é a participação no orçamento total do governo**. A composição não é calculada com função ausente ou denominador zero.
- **Ranking:** ordena apenas as despesas liquidadas nominais para as UFs elegíveis. Não mede resultado, qualidade, eficiência ou gestão.
- **Comparação entre duas UFs:** diferença = valor B − valor A; diferença percentual = diferença / A × 100, se A for diferente de zero. Ambas devem ter o conjunto de funções completo.
- **Evolução histórica:** compara anos de 2021 a 2025; variações percentuais são calculadas apenas para exercícios consecutivos com denominador anterior não nulo. Exercícios ausentes permanecem ausentes, não são interpolados.
- **Regiões:** total regional somente quando todas as UFs da região estão selecionadas e possuem cobertura integral do recorte. A seleção parcial não é rotulada como total regional.
- **Estatísticas descritivas:** média, mediana, extremos e amplitude descrevem os valores das UFs completas na seleção. Não são testes estatísticos nem estimativas de causalidade.
- **Rastreabilidade:** os registros filtrados e as fontes originais ficam disponíveis em tabela e CSV para download.

## Limitações atuais

As três funções selecionadas não representam todas as despesas estaduais. Os valores são nominais, sem deflacionamento pelo IPCA. O Distrito Federal reúne atribuições estaduais e municipais, o que exige cautela em comparações territoriais. **Não há despesas per capita na base oficial** porque a população do IBGE por UF/exercício ainda não foi integrada e validada. As populações da amostra ilustrativa não são utilizadas nessas estatísticas.

## Implementação e verificação

A interface está em `pages/4_Estatisticas.py` (caminho histórico, título visível **Gastos públicos**), `utils/dashboard_ui.py` e `utils/estatisticas_ui.py`; as regras e validações estão em `utils/estatisticas_oficiais.py`; os testes específicos estão em `tests/test_estatisticas_oficiais.py`. As rotas e a coleta de Siconfi permaneceram inalteradas. Execute `python -m pytest -q` na raiz do projeto com a FastAPI e o Streamlit desligados para testar a lógica sem depender da GPU, e depois navegue pelas abas com ambos os servidores ligados. A interface não exige novo download dos pesos do Qwen.
