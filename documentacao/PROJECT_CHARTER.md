# Project Charter — Transparência Brasil (TP3, revisão das rubricas)

## 1. Contexto do projeto

O trabalho mantém o tema original dos TPs 1 e 2: comparação educacional de uma **amostra ilustrativa** de gastos públicos por função em **São Paulo, Goiás e Bahia**, associada ao **ODS 16 — Paz, Justiça e Instituições Eficazes**. As 9 linhas da amostra de 2025 permanecem intactas; não há certificação independente dos valores Siconfi/IBGE indicados nas etiquetas do CSV.

## 2. Problema de negócio revisado

O acesso e interpretação de dados de gastos públicos e documentos sobre transparência podem exigir conhecimento técnico. No TP2, as comparações, a extração Web e o upload/download ficavam em abas e acessavam CSVs locais. No TP3, o problema também envolve **acesso programático por API**, rastreabilidade de fontes e preparação de textos para uso por sistemas de IA.

## 3. Objetivo geral

Oferecer uma solução didática que apresente registros ilustrativos de três estados por meio de uma interface Streamlit multipágina **integrada por HTTP a uma API FastAPI**, amplie o catálogo documental de transparência pública e prepare material com origem rastreável para uso futuro com LLMs.

## 4. Entregas e critérios de aceitação

| Item | Implementação / evidência | Critério verificável |
|---|---|---|
| Navegação multipágina | `app.py`, seis scripts `pages/` | Seis opções no menu lateral, além do início |
| API personalizada | `api/main.py` | GET `/despesas`, `/estatisticas`, `/conteudo-web`, `/health` e POST `/despesas` |
| Integração verdadeira | `utils/api_client.py` + páginas `1`, `2`, `4`, `5` | GET e POST por HTTP, sem depender exclusivamente de leitura local |
| Inclusão de dados Web | `coleta_web.py` | 3 URLs oficiais configuradas (incluindo CGU) e saída CSV/TXT quando executado online |
| Coleta com Selenium | `coleta_selenium.py` | Navegar em URL oficial, aguardar DOM, extrair texto, produzir CSV/TXT somente após sucesso |
| Documentação | `documentacao/` | Charter, Data Summary, API, testes e plano de IA atualizados |
| IA futura | `preparar_llm.py` | JSONL e manifesto com origem, URLs e aviso sobre amostra ilustrativa |
| Qualidade | `tests/` | Testes de contrato GET/POST, cliente HTTP, parsing e Selenium simulado |

## 5. Decisões técnicas

- **FastAPI** fornece uma interface reutilizável para consulta, indicadores e cadastro em `data/registros_manuais.csv` (rotulado como `manual`, sem alterar o CSV acadêmico).
- **Streamlit** consulta a API via `requests`. Para permitir visualização mesmo com a API desligada, algumas páginas apresentam fallback offline **com aviso visível**; essa alternativa não é considerada comunicação com a API.
- **Beautiful Soup** continua sendo a coleta principal por simplicidade e adequação ao HTML de páginas institucionais.
- **Selenium** foi acrescentado para demonstrar aquisição via navegador com espera por conteúdo renderizado. Não se afirma que o portal selecionado exija JavaScript: o navegador foi adotado para atender explicitamente à rubrica.
- **Segregação de proveniência:** números fiscais ilustrativos, conteúdo Web documentado, coletas HTTP/Selenium e cadastros manuais não devem ser confundidos.

## 6. Fontes e escopo

1. Amostra original: `data/amostra_dados.csv` (TP1/TP2), 9 linhas, fontes declaradas Siconfi/IBGE **não auditadas**.
2. ONU/ODS 16: https://brasil.un.org/pt-br/sdgs/16.
3. Tesouro/Siconfi: https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos.
4. **Nova fonte documental:** CGU — https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica.
5. **Fonte para Selenium:** página governamental de informações obrigatórias — https://www.gov.br/acessoainformacao/pt-br/assuntos/transparencia-ativa/informacoes-obrigatorias.
6. Cadastros manuais via FastAPI (sem autenticação e sem equivalência a dados públicos oficiais).

O TP3 **não inclui** autenticação, auditoria de dados fiscais, todos os estados, deploy público seguro, execução de LLM nem evidência automática de que as páginas governamentais sejam exclusivamente dinâmicas.

## 7. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Interpretar amostra como balanço oficial | Avisos de base ilustrativa e separação de origens |
| API desligada | Mensagem de offline e instrução para iniciar Uvicorn |
| POST público não seguro | Somente execução local, registros separados, validação Pydantic |
| Portais ou seletores mudarem | Timeouts, tratamento de erros e logs; revisar fontes quando necessário |
| Selenium sem driver/rede | Configuração explícita e falha sem gerar CSV inventado |
| Confundir síntese Web documentada com scraping executado | Campo `metodo=resumo_documentado_por_consulta_web` e metadados distintos |
| Respostas incorretas de LLM | RAG com URL e evidências, validação humana e aviso de dados ilustrativos |

## 8. Stakeholders

Aluno desenvolvedor, professor avaliador, cidadãos/estudantes interessados em transparência e órgãos provedores de documentação pública (sem participação no desenvolvimento).

## 9. Próximas etapas

No TP seguinte: coleta fiscal reproduzível diretamente em APIs oficiais, recuperação textual com referências, avaliação de LLM por acurácia/fidelidade e regras de privacidade. A coleta executada por Selenium e o uso real do Streamlit devem ser conferidos em máquina com Internet e navegador configurado antes da apresentação.
