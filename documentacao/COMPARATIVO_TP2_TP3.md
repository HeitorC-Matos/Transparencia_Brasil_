# Comparativo TP2 → TP3 (revisão das rubricas)

| Capacidade | TP2 | TP3 revisado |
|---|---|---|
| Navegação | 3 abas numa página | Menu lateral com início e 6 páginas |
| Gráficos e filtros | CSV local | GET `/despesas` por HTTP, fallback local rotulado offline |
| Indicadores | Soma filtrada e gráficos | GET `/estatisticas` integrado e indicador por habitante |
| Upload/download | Sim | Preservados na página Arquivos |
| API FastAPI | Não | 5 rotas com validação e Swagger |
| POST pelo usuário Streamlit | Não | Formulário real POST `/despesas`, com retorno da API |
| Extração Web | 2 fontes via Beautiful Soup | 3 URLs no coletor; novo registro CGU documentado; coleta HTTP real exige rede |
| Selenium | Não | Script WebDriver com espera, parser e saída CSV/TXT; execução externa pendente |
| Qualidade do CSV | Amostra acadêmica | Amostra original intacta, manuais separados, proveniência Web explícita |
| LLM | Ainda não planejado | JSONL rastreável, RAG/resumos e limites documentados |
| Testes | Não apresentados aqui | 21 automatizados aprovados e smoke HTTP real local |

**Distinção essencial:** os três registros Web do pacote não são três scrapes comprovados. O registro CGU é **resumo documental identificado**; após acesso bem-sucedido pela rede, `coleta_web.py` atualiza o registro via Beautiful Soup. O Selenium foi **implementado e simulado** no ambiente de teste, não executado online.
