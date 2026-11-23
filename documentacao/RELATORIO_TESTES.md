# Relatório de testes — Transparência Brasil

## Resultado consolidado

A bateria automatizada executada sobre esta versão do código apresentou **259 testes aprovados, nenhuma falha e oito avisos de depreciação**. Comando:

```powershell
python -m pytest -q
```

Os avisos conhecidos se referem ao uso de um código de status HTTP com nomenclatura deprecada e ao argumento `timeout` do `TestClient` utilizado em alguns testes. Eles não provocaram falhas nesta execução, mas merecem revisão em uma atualização posterior das dependências.

## O que foi testado

| Área | Verificações incluídas |
|---|---|
| API de despesas | GET/POST, validações, filtros, paginação, identificação de origem e preservação da amostra. |
| Cliente HTTP | Comunicação entre componentes, paginação, erros de conexão e tratamento das respostas. |
| Estatísticas da amostra (regressão) | Cálculos ilustrativos anteriores preservados, incluindo despesas por habitante, rankings e comparações. |
| Estatísticas nacionais | Seleção de 27 UFs, soma de funções com cobertura completa, composição percentual, rankings, regiões, perfis, comparação entre UFs, evolução e dados ausentes. |
| Dados oficiais | Tratamento do RREO, seleção das funções e do período, duplicidades, totais, pendências e cobertura de UFs. |
| Conteúdo Web | Extração e transformação de HTML, retenção em falhas e integração dos arquivos de coleta. |
| Selenium | Navegador simulado durante os testes automatizados e leitura do arquivo da coleta real já armazenado. |
| Preparação de corpus | Fragmentação textual, arquivo JSONL, manifesto e segregação de origens. |
| IA e contratos | Requisições válidas e inválidas, `response_model` Pydantic, limites de entrada, saída inconsistente e documentação OpenAPI. |
| Erros | Códigos 422, 429, 500, 503, 504, identificador da requisição e mensagens do cliente. |
| Navegação | Presença e ordem das seis páginas visíveis, sem expor a preparação para IA. |

Os testes automatizados de falhas do Qwen utilizam um serviço de geração simulado e controlado, de modo a não esgotar a GPU. Os testes do coletor Siconfi utilizam respostas construídas para cobrir os casos esperados e de erro; não substituem a validação contábil dos valores declarados.

## Evidências práticas informadas pelo usuário

- **Inferência real:** o Qwen3-4B-Instruct-2507 respondeu a `POST /processar_texto` no Windows com a RTX 4060. Foi relatado uso do processo Python na GPU e geração de resumos.
- **Tempos observados:** aproximadamente 72,9 s na primeira requisição e 12,9 s na segunda requisição com o mesmo exemplo; tempos incluem condições específicas do ambiente local.
- **Integração com a interface:** o usuário confirmou que o Assistente IA funciona no Streamlit e que o menu aparece na ordem definida.
- **Verificação HTTP:** o script `scripts/verificar_erros_http.py` retornou os códigos previstos para `/health` (200), `/ia/health` (200), entrada inválida em `/processar_texto` (422) e rota inexistente (404), com IDs de requisição. Esse script **não carrega o Qwen**.
- **Coleta Siconfi:** o usuário executou a coleta piloto e a nacional. O manifesto da versão atual registra 405 linhas para 27 UFs, 2021–2025, sem pendências.

As evidências descritas como relatadas pelo usuário não são medições produzidas neste ambiente. O funcionamento com a conexão de Internet fisicamente desligada ainda não foi comprovado por um relato de teste específico. A coleta nacional continua sujeita à conferência amostral com os demonstrativos originais.

## Verificações locais recomendadas antes de apresentar o projeto

1. Iniciar a FastAPI com um único worker e confirmar `http://127.0.0.1:8000/docs`.
2. Iniciar o Streamlit e conferir as seis páginas visíveis; abrir **Gastos públicos**, testar os filtros comuns, os gráficos, as seis análises detalhadas e os insights com Qwen.
3. Conferir que o painel **Gastos públicos** utiliza somente Siconfi; a amostra ilustrativa permanece armazenada apenas para histórico e testes.
4. Executar `python scripts/verificar_erros_http.py` com a FastAPI ligada.
5. Enviar uma entrada inválida à rota `POST /processar_texto` e confirmar HTTP 422.
6. Enviar uma entrada válida e conferir o resultado real do Qwen pela interface.
7. Examinar `data/siconfi/manifesto.json` e comparar, por amostragem, valores com as declarações originais.
8. Quando possível, registrar um teste de reinício e inferência sem acesso à Internet para comprovar o modo completamente offline.

O objetivo desses passos é manter separadas as evidências de teste automatizado, as verificações HTTP e o funcionamento real da aplicação.

## Histórico de testes — sumarização documental e síntese fiscal

Na versão que acrescentou a automação documental, a bateria local foi executada com **221 testes aprovados, oito avisos de depreciação e nenhuma falha**. São abrangidos os testes de catálogo e metadados dos quatro documentos, geração de prompts em três versões, sumarização em trechos, rejeição de textos acima do limite, conferência de cálculos fiscais em `Decimal`, identificação de lacunas na cobertura e contratos das novas rotas e do cliente HTTP.

**Limite da evidência:** nesse ambiente não foram carregados pesos de Qwen nem executada inferência real na GPU. Os testes de geração empregaram retorno controlado (mock), verificando orquestração, validações e tratamento de erros. Para concluir a validação prática da nova funcionalidade, o usuário deve executar `scripts/teste_sumarizacao_http_real.py --fiscal` na máquina com a RTX 4060 e conferir os resumos em relação às fontes. Posteriormente, o autor executou a comparação real entre três versões de prompts no Qwen local. O resultado, que não faz parte da bateria simulada, está preservado em `documentacao/experimentos/avaliacao_prompts_final.json`.


## Histórico de testes — perguntas sobre dados fiscais

Na etapa de perguntas fiscais, a bateria passou em **221 testes** sem falhas, com 8 avisos de depreciação do ambiente de testes. Testes em `tests/test_perguntas_fiscais.py` e `tests/test_cliente_perguntas.py` cobrem as cinco operações, cobertura e consistência de valores, contratos HTTP, entradas inválidas, segregação de fontes, utilização opcional do modelo e fallback quando a GPU está indisponível. O autor informou que executou a aplicação completa em sua instalação local e não encontrou problemas. Essa validação manual complementa a simulação, mas não altera o caráter automatizado dos 259 testes da versão atual. Essa etapa foi documentada como histórica e não substitui a evidência de saída real do Qwen nos testes realizados.


## Histórico de testes — dashboard na versão inicial da página App

Na integração do dashboard final, a bateria completa alcançou **240 testes aprovados, oito avisos e nenhuma falha**. Os testes específicos do painel verificam o uso exclusivo dos registros oficiais, cobertura de combinações UF/ano/função, exclusão de UFs incompletas, tratamento distinto de ausência e valor zero, filtros inválidos, séries históricas, fontes e alimentação pela rota HTTP da FastAPI.

Uma execução HTTP real local (sem pesos do Qwen) confirmou 405 registros no manifesto, 81 registros de 2025, 27 UFs no exercício e quatro documentos institucionais catalogados. Uma simulação da renderização Streamlit percorreu os componentes de exibição e gerou dois gráficos de barras, um gráfico de linhas e indicadores, mas **não substitui o teste do navegador real nem comprova inferência GPU**. O novo dashboard permite geração apenas a pedido do usuário e mantém os resultados fiscais calculados pelo Python.

Verificação externa para a instalação local: `python scripts/verificar_dashboard.py`; validação manual e limitações: `documentacao/DASHBOARD_INTEGRADO.md`.


## Validação da organização definitiva — App e Gastos públicos

Na reorganização da interface, a bateria completa executada apresentou **243 testes aprovados, oito avisos de depreciação e nenhuma falha**. A página App foi convertida em apresentação do projeto e do ciclo de Ciência de Dados. O dashboard passou à página visível **Gastos públicos**, com filtros únicos, análises estatísticas detalhadas e insights do Qwen. A antiga página ilustrativa foi removida apenas da navegação. Os testes de regressão confirmam a separação dos papéis, a preservação da amostra histórica e o reaproveitamento da base oficial. O autor informou posteriormente ter testado a aplicação completa no navegador e a integração com o Qwen sem identificar problemas. Os testes automatizados, por si só, continuam independentes da validação manual e da inferência real na GPU.


## Verificação manual atual e experimento de prompts

Na avaliação final, o autor informou que **executou o código completo e testou a aplicação no computador local sem encontrar problemas**. A informação é apresentada como relato de teste manual; não foi criada uma métrica de usabilidade ou um relatório instrumental que não exista. O experimento real com o Qwen e os três prompts foi executado e está disponível em `documentacao/experimentos/avaliacao_prompts_final.json`. O limite padrão de 384 tokens foi preservado. A execução totalmente desconectada da Internet e uma aferição exata de VRAM não foram demonstradas; o código, contudo, impede acesso ao Hugging Face Hub durante a inferência depois de os pesos estarem instalados.


## Integração do ODS 16 e Governança no Assistente IA

Nesta etapa foram acrescentados testes em `tests/test_ods16_interativo.py`. A versão atual apresentou **259 testes aprovados, oito avisos e nenhuma falha**. Os testes verificam: detecção de perguntas institucionais, preservação das consultas fiscais, leitura real do documento da ONU coletado com Beautiful Soup, extração das metas 16.6 e 16.10, contrato HTTP do tipo `ods16`, retorno factual sem Qwen, simulação controlada da geração, falha da GPU sem perda das fontes, resposta 503 quando a fonte não está disponível e existência da nova categoria da interface. O teste de geração é simulado; não demonstra inferência nova com a GPU do usuário. A evidência passa a ser a funcionalidade interativa, não um documento avulso.
