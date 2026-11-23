# Experimento de engenharia de prompts — execução local

## Avaliação experimental de engenharia de prompts

Foi realizado um experimento utilizando o modelo local Qwen3-4B-Instruct-2507 e um documento institucional obtido por web scraping sobre a API de Dados Abertos do Siconfi.

Foram avaliadas três estratégias de engenharia de prompts: Básico, Estruturado e Fundamentado. As execuções utilizaram o mesmo documento e o mesmo limite máximo de geração de 384 tokens.

Os prompts Básico e Estruturado produziram resumos completos, com 147 e 150 palavras, respectivamente. Ambos apresentaram boa cobertura das informações centrais, clareza e aderência geral ao documento.

O prompt Fundamentado gerou 242 palavras e atingiu o limite de 384 tokens antes de concluir a resposta. Também apresentou afirmações não comprovadas pelo documento original e dedicou parte significativa da resposta a limitações que não constituíam o objeto central do texto.

O experimento demonstrou que a formulação das instruções influencia a qualidade da sumarização e que prompts mais elaborados não necessariamente produzem respostas superiores. Evidenciou também a importância de controlar a extensão da geração e evitar instruções que induzam o modelo a abordar assuntos não contemplados na fonte.

Os resultados referem-se a uma execução por configuração e a um único documento, não permitindo generalizações estatísticas sobre o desempenho dos prompts.

**Evidência original:** [`experimentos/avaliacao_prompts_final.json`](experimentos/avaliacao_prompts_final.json). O JSON preserva as respostas e métricas coletadas na GPU local, mantendo nulos os campos de avaliação humana, sem atribuir notas automaticamente.

**Parâmetros:** durante esta execução foi utilizada uma instrução temporária para obter aproximadamente 150 a 180 palavras por resumo. A instrução foi retirada do código definitivo; o limite máximo de geração permanece em **384 tokens**. O script permite repetir o experimento com as instruções atuais, mas o resultado poderá variar.
