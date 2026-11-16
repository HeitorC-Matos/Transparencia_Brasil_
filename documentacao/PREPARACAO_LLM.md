# Preparação do corpus documental para LLMs

## Situação atual

A rotina de preparação de dados não executa nem treina um modelo de IA. O comando `python preparar_llm.py` produz `data/llm/documentos.jsonl` e `manifesto.json`. A última geração registrada em `manifesto.json` ocorreu em **16/11/2026 às 16:12:21 UTC**, com **16 fragmentos**: **7 fragmentos Web** (4 páginas distintas) e **9 descrições de despesas ilustrativas e não auditadas**. Os 7 fragmentos Web correspondem a ONU/ODS 16 (2), Tesouro/Siconfi (2), CGU (1) e Selenium/LAI (2). O fracionamento de textos longos explica por que 4 fontes Web geram 7 trechos.

Os registros Web incluem título, URL, `metodo`, `data_coleta` e texto; os registros fiscais trazem fonte nominal e `verificado_em_fonte_oficial=false`. Os cadastros manuais por POST ficam de fora. **O conteúdo Selenium de 19/10/2026 já integra o corpus** (2 fragmentos com método `selenium+chromium`); os três registros Beautiful Soup também estão incluídos. Caso alguma fonte seja novamente coletada, basta executar `python preparar_llm.py` para atualizar os arquivos.

## Aplicações propostas

- **Q&A / RAG:** consultar trechos por relevância e apresentar respostas com URL/documento de suporte; se não houver evidência, responder que não está disponível.
- **Resumos institucionais:** sintetizar informações sobre ODS 16, Siconfi, CGU e obrigações de transparência sem retirar contexto.
- **Relatórios descritivos:** explicar gráficos educacionais usando a amostra local, sempre rotulando os valores como ilustrativos.
- **Análise de sentimentos:** não adequada à base atual (tabelas numéricas e textos administrativos). Futuramente exigiria opiniões de uma fonte apropriada e respeitando privacidade.

## Critérios para o próximo TP

1. Recuperar documentos pelo conteúdo e metadados.
2. Exigir fontes verificáveis e impedir interpretação de comandos escondidos nos textos Web.
3. Rastrear se cada saída do LLM é apoiada no conteúdo indexado.
4. Medir alucinação, fidelidade e custo; testar perguntas sem resposta.
5. Validar os dados numéricos na fonte fiscal antes de tirar conclusões reais.
6. Revisar LGPD, retenção, segurança da API e tratamento de entrada do usuário.

**Exemplo de restrição:** se a pergunta for "quanto foi gasto oficialmente em Educação em São Paulo?", a base atual só contém valor acadêmico não validado e o assistente deve explicar essa limitação, não afirmar um total oficial.
