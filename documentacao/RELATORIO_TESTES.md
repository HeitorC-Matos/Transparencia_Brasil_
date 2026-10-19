# Relatório de testes — TP3 (revisão das rubricas)

**Data:** 19/10/2026

## Resultado automatizado

**21 testes aprovados**, comando `python -m pytest -q`. Prova ponta a ponta separada: `python -m scripts.teste_http_real` (**aprovada**). As verificações abrangem:

| Eixo | Evidências |
|---|---|
| Streamlit multipágina | Arquivos de 6 páginas e sintaxe verificada |
| API FastAPI | GET `/health`, `/despesas`, `/estatisticas`, `/conteudo-web`, validação, filtros e paginação |
| Integração da interface | Cliente `utils/api_client.py` executa GET e POST contra `TestClient(FastAPI)`; testou consulta, criação, leitura posterior, fallback e isolamento dos dados |
| Fluxo HTTP de rede real | Subimos **Uvicorn em porta localhost** e enviamos `requests` reais a `/health` e `/despesas`, seguido por POST `/despesas` e nova leitura manual |
| Coleta Beautiful Soup | HTML sintético: extração, remoção de menus, CSV/TXT, metadados e retenção em falhas |
| Selenium | Navegador simulado comprova chamada `get(url)`, espera injetável, parsing e CSV/TXT; página vazia é recusada |
| Integração Selenium → API | CSV Selenium sintético em pasta temporária passou a ser retornado por GET `/conteudo-web` |
| Estatísticas | Formatação monetária e indicadores por habitante |
| IA futura | Fragmentação, corpus JSONL, metadados e segregação de cadastros manuais |

**Outras verificações:** `compileall` para todos os scripts, `preparar_llm.py` gerando **12 documentos** (3 Web + 9 fiscais), leitura das três URLs configuradas no código e verificação de integridade do CSV original de nove linhas.

**Aviso sobre os testes Selenium:** a coleta em site remoto **não pôde ser executada** neste ambiente porque não há acesso aos portais externos, nem biblioteca Selenium e ChromeDriver disponíveis. Os testes de navegador simulado só comprovam o comportamento do nosso coletor isolado. **Não contar esses testes como extração governamental online.** O código está pronto para executar no computador com as dependências completas.

**Aviso sobre interface visual:** o pacote `streamlit` não estava instalado no ambiente de verificação, e a instalação remota de dependências não foi possível. Assim, as páginas foram verificadas sintaticamente e o cliente HTTP foi testado, mas **não executamos a navegação visual real** do Streamlit. Isso deve ser conferido localmente.

## Roteiro de aceitação manual (apresentação)

1. Instalar dependências: `python -m pip install -r requirements.txt`.
2. No terminal 1: `uvicorn api.main:app --reload`; verificar `/health` e `/docs`.
3. No terminal 2: `streamlit run app.py`; verificar menu com 6 páginas, filtros, gráficos, upload/download e nuvem de palavras.
4. Em Gastos: conferir mensagem **"Dados consultados na FastAPI"**, mudar filtros e ver resposta.
5. Em Estatísticas: conferir **GET /despesas e GET /estatisticas** e expandir o resumo retornado.
6. Em Conteúdo Web: conferir **GET /conteudo-web** e tabela com 3 registros (antes de Selenium real).
7. Em **API FastAPI**, testar filtro GET, enviar POST com um valor ilustrativo, atualizar a página e consultar origem `manual`; confirmar que o registro aparece e tem `origem=manual`.
8. Verificar que `data/amostra_dados.csv` permanece intacto após POST; novos dados estão somente em `data/registros_manuais.csv` (não versionado).
9. Com Internet: rodar `python coleta_web.py` e confirmar fonte CGU com `metodo=requests+beautifulsoup` e timestamp preenchido. Se falhar, guardar saída do erro; não alegar sucesso.
10. Com Selenium e ChromeDriver instalados e Internet: rodar `python coleta_selenium.py`; confirmar CSV/TXT gerados com `metodo=selenium+chromium` e fonte oficial, depois conferir a nova linha pelo GET `/conteudo-web` e na interface.
11. Rodar `python preparar_llm.py` e confirmar atualização do manifesto (12 documentos antes de Selenium; pode aumentar).
12. Executar novamente `python -m pytest -q`.

## Checklist por rubrica

| Rubrica | Evidência criada | Confirmação no ambiente atual |
|---|---|---|
| 1. Menu multipágina | 6 scripts em `pages/` | Sintaxe e estrutura aprovadas; visual pendente |
| 2. API FastAPI | 5 rotas em `api/main.py` | GET/POST aprovados |
| 3. Integração Streamlit/API | `utils/api_client.py` + páginas 1,2,4,5 | Cliente HTTP real e servidor local aprovados; visual pendente |
| 4. Mais dados Web | nova fonte CGU no catálogo e coletor BS configurado | Nova página documentada; coleta HTML externa pendente |
| 5. Selenium | `coleta_selenium.py` | Código e simulação aprovados; execução remota pendente |
| 6. Documentos revisados | Charter e Data Summary | Atualizados |
| 7. Plano LLM | Preparação JSONL, 12 textos, documentação | Gerado e testado |

Os itens pendentes **não são apresentados como já executados**.
