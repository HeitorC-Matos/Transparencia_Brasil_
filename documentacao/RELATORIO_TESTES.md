# Relatório de testes — Transparência Brasil

## Resultado consolidado

A bateria automatizada executada sobre esta versão do código apresentou **130 testes aprovados, nenhuma falha e oito avisos de depreciação**. Comando:

```powershell
python -m pytest -q
```

Os avisos conhecidos se referem ao uso de um código de status HTTP com nomenclatura deprecada e ao argumento `timeout` do `TestClient` utilizado em alguns testes. Eles não provocaram falhas nesta execução, mas merecem revisão em uma atualização posterior das dependências.

## O que foi testado

| Área | Verificações incluídas |
|---|---|
| API de despesas | GET/POST, validações, filtros, paginação, identificação de origem e preservação da amostra. |
| Cliente HTTP | Comunicação entre componentes, paginação, erros de conexão e tratamento das respostas. |
| Estatísticas da amostra | Composição percentual, despesas por habitante, rankings, comparações, valores ausentes e dados inconsistentes. |
| Dados oficiais | Tratamento do RREO, seleção das funções e do período, duplicidades, totais, pendências e cobertura de UFs. |
| Conteúdo Web | Extração e transformação de HTML, retenção em falhas e integração dos arquivos de coleta. |
| Selenium | Navegador simulado durante os testes automatizados e leitura do arquivo da coleta real já armazenado. |
| Preparação de corpus | Fragmentação textual, arquivo JSONL, manifesto e segregação de origens. |
| IA e contratos | Requisições válidas e inválidas, `response_model` Pydantic, limites de entrada, saída inconsistente e documentação OpenAPI. |
| Erros | Códigos 422, 429, 500, 503, 504, identificador da requisição e mensagens do cliente. |
| Navegação | Presença e ordem das sete páginas visíveis, sem expor a preparação para IA. |

Os testes automatizados de falhas do Qwen utilizam um serviço de geração simulado e controlado, de modo a não esgotar a GPU. Os testes do coletor Siconfi utilizam respostas construídas para cobrir os casos esperados e de erro; não substituem a validação contábil dos valores declarados.

## Evidências práticas informadas pelo usuário

- **Inferência real:** o Qwen3-4B-Instruct-2507 respondeu a `POST /processar_texto` no Windows com a RTX 4060. Foi relatado uso do processo Python na GPU e geração de resumos.
- **Tempos observados:** aproximadamente 72,9 s na primeira requisição e 12,9 s na segunda requisição com o mesmo exemplo; tempos incluem condições específicas do ambiente local.
- **Integração com a interface:** o usuário confirmou que o Assistente IA funciona no Streamlit e que o menu aparece na ordem definida.
- **Verificação HTTP:** o script `scripts/verificar_questao4.py` retornou os códigos previstos para `/health` (200), `/ia/health` (200), entrada inválida em `/processar_texto` (422) e rota inexistente (404), com IDs de requisição. Esse script **não carrega o Qwen**.
- **Coleta Siconfi:** o usuário executou a coleta piloto e a nacional. O manifesto da versão atual registra 405 linhas para 27 UFs, 2021–2025, sem pendências.

As evidências descritas como relatadas pelo usuário não são medições produzidas neste ambiente. O funcionamento com a conexão de Internet fisicamente desligada ainda não foi comprovado por um relato de teste específico. A coleta nacional continua sujeita à conferência amostral com os demonstrativos originais.

## Verificações locais recomendadas antes de apresentar o projeto

1. Iniciar a FastAPI com um único worker e confirmar `http://127.0.0.1:8000/docs`.
2. Iniciar o Streamlit e conferir o menu e as cinco seções da página Estatísticas.
3. Consultar a base ilustrativa e a base Siconfi sem misturar origens.
4. Executar `python scripts/verificar_questao4.py` com a FastAPI ligada.
5. Enviar uma entrada inválida à rota `POST /processar_texto` e confirmar HTTP 422.
6. Enviar uma entrada válida e conferir o resultado real do Qwen pela interface.
7. Examinar `data/siconfi/manifesto.json` e comparar, por amostragem, valores com as declarações originais.
8. Quando possível, registrar um teste de reinício e inferência sem acesso à Internet para comprovar o modo completamente offline.

O objetivo desses passos é manter separadas as evidências de teste automatizado, as verificações HTTP e o funcionamento real da aplicação.
