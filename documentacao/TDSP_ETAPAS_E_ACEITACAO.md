# Etapas do TDSP e aceitação da solução

O projeto foi organizado pelas cinco fases do TDSP:

1. **Compreensão do negócio:** dificuldade do cidadão em entender informações fiscais; ODS 16; público-alvo e limites do recorte.
2. **Aquisição e compreensão dos dados:** coleta oficial no Siconfi, textos com Beautiful Soup/Selenium e manutenção de metadados de origem.
3. **Modelagem:** cálculos estatísticos em Python e explicações e resumos com Qwen, usando engenharia de prompts.
4. **Implantação:** interface Streamlit, API FastAPI, páginas organizadas e pacotes de distribuição do código.
5. **Aceitação:** testes de regras fiscais, APIs, páginas e organização. A versão atual teve **259 testes automatizados aprovados e oito avisos**, mas ainda não houve teste formal de usabilidade com cidadãos.

## Evidências

- `data/siconfi/manifesto.json`: 27 UFs, 2021–2025, 405 registros.
- `data/conteudo_web.csv` e `data/conteudo_selenium.csv`: quatro textos institucionais.
- `data/llm/manifesto.json`: 16 fragmentos preparados para IA.
- `documentacao/experimentos/avaliacao_prompts_final.json`: resultados reais das três versões de prompt.
- `tests/`: testes automatizados de dados, API, IA e interface.

## Validação e controles remanescentes

O autor informou ter **executado a aplicação completa no computador local sem identificar problemas**, incluindo a navegação, a interface e as funcionalidades com Qwen. Essa validação manual complementa, mas não substitui, os **259 testes automatizados** documentados no projeto.

Como verificação técnica complementar, permanece recomendada a **conferência amostral dos valores extraídos com os demonstrativos originais do Siconfi**. A estrutura da base foi validada, mas a aplicação não realiza auditoria independente dos dados declarados.
