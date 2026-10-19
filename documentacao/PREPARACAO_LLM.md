# Preparação para integração futura com LLMs — TP3

## Situação atual

Não é executado nem treinado modelo de IA nesta etapa. A rotina `python preparar_llm.py` produz `data/llm/documentos.jsonl` e `manifesto.json`. Atualmente são **12 documentos**: 3 registros Web e 9 descrições de despesas **ilustrativas e não auditadas**.

Os registros Web incluem título, URL, `metodo` (para identificar extração automatizada ou **resumo documentado**), data disponível e texto; os registros fiscais têm fonte nominal indicada e `verificado_em_fonte_oficial=false`. Os cadastros manuais por POST ficam de fora. Se o Selenium conseguir coletar e salvar `data/conteudo_selenium.csv`, rodar `preparar_llm.py` novamente incorporará a fonte no corpus.

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
