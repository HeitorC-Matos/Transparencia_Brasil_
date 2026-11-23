# ODS 16 e Governança — função interativa do Assistente IA

O Transparência Brasil possui uma função de explicação do **ODS 16** dentro do próprio aplicativo. A implementação integra a **mesma rota** `POST /ia/perguntar_dados` em dois pontos da interface: **Perguntar aos dados** e a categoria própria **ODS 16 e Governança**.

## Problema que a função resolve

Antes, o usuário conseguia resumir a página da ONU sobre o ODS 16, mas o modelo não recebia uma descrição verificável das funcionalidades do Transparência Brasil para explicar a relação entre os dois. Agora o sistema reúne as informações do projeto com o texto coletado, de modo que o Qwen possa gerar uma explicação contextualizada.

## Funcionamento técnico

1. O serviço identifica se a pergunta trata de ODS 16, das metas 16.6/16.10, Governança ESG ou do Transparência Brasil. As consultas fiscais comuns permanecem no motor Python de cálculo.
2. Lê `data/ods16/contexto_projeto.json` com objetivo, funcionalidades, recorte dos dados, aplicação da IA e limitações documentadas do projeto.
3. Busca `https://brasil.un.org/pt-br/sdgs/16` no catálogo derivado do arquivo `data/conteudo_web.csv`, coletado por `requests+beautifulsoup`, e recupera somente as metas 16.6 e 16.10. **Não há nova consulta à Internet durante a pergunta.**
4. Produz uma resposta factual mínima, com fontes, mesmo quando o Qwen está desativado.
5. Se habilitado, encaminha ao Qwen3-4B-Instruct-2507 apenas os fatos preparados e um foco de explicação controlado; o modelo retorna a explicação em português, em até 384 tokens.
6. A interface distingue fatos documentados e a explicação de IA, apresenta as fontes e informa as limitações do alcance dos dados.

## Teste no aplicativo

Com a FastAPI e o Streamlit iniciados, experimente as perguntas abaixo nas duas entradas:

- Como o Transparência Brasil está relacionado ao ODS 16?
- Como o projeto contribui para a meta 16.6?
- O que a meta 16.10 tem a ver com o acesso à informação pública?
- Como a Governança ESG se relaciona com o dashboard?

Depois pergunte **“Quanto Goiás gastou com Saúde em 2024?”** em Perguntar aos dados para confirmar que a consulta numérica continua independente. O modelo pode gerar uma redação diferente a cada execução, mas não deve criar informações fora das fontes apresentadas. Os testes automatizados verificam as estruturas e o roteamento; a geração real deve ser testada na máquina com o Qwen instalado.

## Alcance da relação ODS/ESG

A meta **16.6** trata de instituições eficazes, responsáveis e transparentes. A **16.10** aborda o acesso público à informação. O projeto oferece acesso interativo a despesas liquidadas de três funções do RREO para as 27 UFs e explicações acessíveis. Isso pode apoiar transparência e controle social, relacionados à dimensão Governança (G) do ESG. A aplicação **não calcula indicadores de impacto ESG, não comprova cumprimento do ODS e não avalia eficiência ou desempenho dos governos**.

Fonte original coletada: https://brasil.un.org/pt-br/sdgs/16; descrição do projeto: `README.md` e `data/ods16/contexto_projeto.json`.
