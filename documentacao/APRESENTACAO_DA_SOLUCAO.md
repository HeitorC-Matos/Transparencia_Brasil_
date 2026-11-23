# Transparência Brasil
## Tarefa 4 — Apresentação e argumentação da solução final

Novembro de 2026


# APRESENTAÇÃO

Nesta tarefa, apresento a versão final do Transparência Brasil e explico como as partes do projeto se relacionam com o problema que escolhi no início do trabalho. A proposta surgiu da dificuldade que muitas pessoas têm para encontrar, comparar e entender dados sobre despesas públicas. Por isso, desenvolvi uma aplicação que reúne informações fiscais, organiza esses valores em gráficos e utiliza inteligência artificial para ajudar na leitura dos resultados.

A apresentação foi organizada seguindo o ciclo de Ciência de Dados: definição do problema, coleta, preparação, análise, uso do modelo de IA e disponibilização dos resultados. Também explico a relação com o ODS 16 e a governança ESG, mostro o que foi testado e registro os principais limites da solução.


# 1 O PROBLEMA DE NEGÓCIO E A SOLUÇÃO


## 1.1 Problema identificado

As informações sobre gastos públicos estão disponíveis em portais e bases oficiais, mas normalmente exigem que a pessoa conheça os nomes dos demonstrativos, as classificações contábeis e a forma de consultar os dados. Isso dificulta a comparação entre estados e pode afastar cidadãos que só querem compreender para onde estão sendo destinados determinados recursos.

O problema que procurei enfrentar não foi a falta de publicação dos dados, mas a dificuldade de transformar esses registros em informações claras. Uma tabela extensa pode conter os valores necessários, mas nem sempre permite perceber rapidamente diferenças entre estados ou mudanças ao longo dos anos.


## 1.2 O que foi desenvolvido

O Transparência Brasil reúne um dashboard em Streamlit, uma API em FastAPI, dados fiscais do Siconfi, documentos institucionais coletados pela Web e um assistente baseado no modelo local Qwen3-4B-Instruct-2507. O usuário pode selecionar uma ou várias unidades da Federação, escolher um exercício, comparar despesas e solicitar explicações sobre o que está vendo.

O projeto começou com uma proposta concentrada em São Paulo, Goiás e Bahia. Durante o desenvolvimento, a base utilizada no painel foi ampliada para as 27 unidades da Federação e passou a contemplar os exercícios de 2021 a 2025. A página Gastos públicos concentra o dashboard, enquanto a página App apresenta o projeto sem repetir os mesmos gráficos.

A solução não pretende avaliar qual governo é melhor ou afirmar que uma despesa maior produz um serviço público melhor. Seu objetivo é tornar os dados consultáveis e compreensíveis, deixando as fontes disponíveis para conferência.


# 2 COMO O CICLO DE CIÊNCIA DE DADOS FOI APLICADO


## 2.1 Definição do problema e planejamento

A primeira etapa foi entender o público que poderia utilizar o sistema e decidir quais perguntas o projeto deveria ajudar a responder. Entre elas estão: quanto uma UF declarou de despesas liquidadas em determinada função, como esses valores mudaram com o tempo e como se comparam os estados no mesmo exercício.

O TDSP foi utilizado para organizar o trabalho desde essa definição até os testes. Ao longo da construção, o escopo foi ajustado para aproveitar uma base fiscal nacional e integrar um modelo de linguagem, sem abandonar a finalidade inicial de facilitar o entendimento das informações públicas.


## 2.2 Coleta dos dados

A principal fonte dos valores fiscais é a API de Dados Abertos do Siconfi, do Tesouro Nacional. O script de coleta consulta o RREO, Anexo 02, do sexto bimestre e seleciona as despesas liquidadas acumuladas nas funções Educação, Saúde e Segurança Pública. Os registros são armazenados no arquivo data/siconfi/despesas_oficiais.csv, acompanhado de um manifesto com a cobertura e os critérios utilizados.

O arquivo distribuído no projeto possui 405 registros: 27 UFs, cinco exercícios (2021 a 2025) e três funções. Esses são dados declarados ao Siconfi, apresentados em valores nominais. O projeto não realizou uma auditoria independente de cada lançamento contábil.

Também foram coletados documentos institucionais com Requests e Beautiful Soup, incluindo conteúdos sobre o ODS 16, a API do Siconfi e transparência pública. Uma coleta adicional utilizou Selenium e Chromium para registrar conteúdo governamental sobre transparência ativa. Esses textos são guardados com informações de origem e são utilizados principalmente nas ferramentas de sumarização.


**Quadro 1 — Dados utilizados no projeto**

| Conjunto | Origem e cobertura | Utilização na aplicação |
| --- | --- | --- |
| Dados fiscais | Siconfi; 27 UFs, 2021–2025, três funções; 405 registros | Gráficos, rankings, comparações, séries históricas e explicações fiscais. |
| Documentos da Web | Três páginas institucionais via Requests/Beautiful Soup | Consulta do conteúdo e resumos pelo Qwen. |
| Documento coletado com Selenium | Uma página governamental com coleta registrada | Consulta documental e sumarização. |


## 2.3 Limpeza, organização e preparação

Depois da coleta, o Python padroniza os campos, identifica a UF, o ano, a função e o tipo de despesa, verifica duplicidades e confere as combinações esperadas. Os dados não encontrados são tratados como ausentes, em vez de receberem automaticamente o valor zero. Isso é importante porque um registro faltante não significa que o governo não realizou aquela despesa.

Os documentos textuais também passam por organização e identificação das fontes. Para o uso com IA, o sistema recupera os textos armazenados, prepara as instruções e pode dividir conteúdos longos em partes menores antes de produzir um resumo consolidado. Os dados ilustrativos utilizados no início do desenvolvimento ficaram separados da base oficial que alimenta o dashboard.


## 2.4 Análise estatística e visualização

Com os dados organizados, a aplicação calcula valores e indicadores em Python. O dashboard apresenta gráficos de barras, rankings de UFs, evolução histórica, comparações diretas, perfis estaduais e estatísticas descritivas. Os filtros permitem escolher uma ou várias UFs, exercícios e funções de governo.

As diferenças absolutas e percentuais, somas, médias e demais cálculos são realizados antes da geração de texto pela IA. No painel, o total apresentado para uma UF corresponde ao conjunto de funções selecionadas. Quando as três funções estão marcadas, trata-se do subtotal de Educação, Saúde e Segurança Pública, e não de todo o orçamento estadual.

As comparações são nominais. Isso significa que os gráficos ajudam a identificar diferenças nos valores declarados, mas não medem, sozinhos, eficiência administrativa, poder de compra corrigido pela inflação ou qualidade dos serviços públicos.


## 2.5 Uso de inteligência artificial e engenharia de prompts

Para a etapa de inteligência artificial, escolhi a automação de sumarização de textos com um modelo local. O Qwen3-4B-Instruct-2507 permite que o usuário selecione um documento já coletado e peça um resumo executivo, os pontos principais ou uma explicação mais simples. O sistema também pode enviar indicadores fiscais calculados ao modelo para produzir uma explicação em linguagem natural.

Essa separação é uma decisão importante do projeto: o Python encontra os registros e calcula os valores; o Qwen transforma as informações em texto. Assim, o modelo não precisa inventar números nem fazer as contas que já podem ser verificadas no código.

Na engenharia de prompts, foram utilizadas as versões Básico, Estruturado e Fundamentado. Fiz um experimento com o mesmo documento institucional sobre a API do Siconfi, mantendo o modelo e o limite de geração de 384 tokens. Os prompts Básico e Estruturado produziram resumos completos. O Fundamentado atingiu o limite de tokens e terminou incompleto, além de incluir observações que exigem conferência com o texto original.

Esse experimento mostrou que instruções mais detalhadas nem sempre geram respostas melhores. O resultado foi registrado em documentacao/experimentos/avaliacao_prompts_final.json. As notas de qualidade não foram calculadas automaticamente; a fidelidade e a clareza dependem de leitura e avaliação do conteúdo.


## 2.6 Disponibilização da solução

A aplicação foi organizada em duas partes: o Streamlit apresenta a interface e recebe as escolhas do usuário, enquanto a FastAPI disponibiliza os serviços e as consultas. O modelo Qwen funciona localmente no computador utilizado para os testes, sem depender de uma API comercial para gerar o texto.

A página App explica a proposta. Gastos públicos reúne gráficos, indicadores, análises e insights com Qwen. Dados oficiais permite consultar os registros e suas fontes. Conteúdo da Web apresenta os documentos coletados. Assistente IA recebe perguntas sobre despesas, produz resumos documentais e permite processar textos livres. A página API FastAPI apresenta os serviços disponíveis.


# 3 DEMONSTRAÇÃO DO DASHBOARD FINAL

A navegação foi simplificada para que as informações não apareçam repetidas em várias páginas. O usuário começa conhecendo a proposta na página App e pode seguir para Gastos públicos quando deseja analisar os valores fiscais. No mesmo painel, ele seleciona o recorte, observa os gráficos e pode pedir ao Qwen uma explicação do resultado.


**Quadro 2 — Exemplo de apresentação da solução**

| Etapa de uso | O que o usuário faz | O que a aplicação entrega |
| --- | --- | --- |
| Consulta fiscal | Escolhe SP, GO e BA, ano de 2025 e Educação. | Gráfico comparativo e valores declarados para o recorte. |
| Análise com IA | Solicita explicação dos gráficos selecionados. | Texto produzido pelo Qwen a partir dos valores calculados pelo Python. |
| Pergunta em linguagem natural | Pergunta qual UF apresentou a maior despesa liquidada com Educação em 2025. | Resposta calculada com ranking, exercício e indicação da fonte. |
| Sumarização | Seleciona o documento sobre a API do Siconfi. | Resumo do texto coletado, com identificação da origem. |
| Conferência | Abre Dados oficiais ou as informações de fonte. | Registros e critérios para verificar o resultado. |

Esses exemplos mostram as funcionalidades disponíveis, não resultados numéricos fabricados para a apresentação. Os valores concretos são recuperados da base do Siconfi quando o usuário executa a consulta.

O dashboard permite explorar os dados sem exigir que o usuário escreva código ou consulte diretamente a documentação de uma API. Para mim, esse é um dos principais ganhos do projeto: colocar a informação oficial e sua explicação no mesmo ambiente.


# 4 RELAÇÃO COM GOVERNANÇA, ODS E ESG

O Transparência Brasil está relacionado principalmente ao ODS 16 — Paz, Justiça e Instituições Eficazes. As metas 16.6, sobre instituições eficazes, responsáveis e transparentes, e 16.10, sobre acesso público à informação, têm ligação com a proposta de facilitar o acompanhamento de dados fiscais pelos cidadãos.

Na abordagem ESG, a contribuição mais direta é para o componente G, de Governança. Ao reunir fontes oficiais, registrar a metodologia e permitir que os resultados sejam conferidos, o sistema apoia a transparência e o controle social. As despesas com Saúde e Educação também tratam de áreas importantes para a sociedade, mas o projeto não mede, por si só, o impacto social dessas políticas.

O componente ambiental do ESG não foi mensurado nesta versão. Também não seria correto concluir que um estado tem boa governança apenas porque declarou valores maiores em determinada função. O dashboard permite acompanhar e questionar informações; a avaliação dos resultados das políticas públicas exige outros dados e métodos.


# 5 POR QUE A SOLUÇÃO ESCOLHIDA É ADEQUADA

Escolhi trabalhar com dados oficiais porque a proposta depende de valores que possam ser rastreados até uma fonte pública. A coleta automatizada facilita a repetição do processo e reduz o trabalho de preencher tabelas manualmente. O tratamento e a validação dos registros ajudam a organizar um conjunto grande de informações antes da comparação.

Os gráficos são importantes porque permitem perceber rapidamente diferenças que seriam mais difíceis de observar em listas extensas. A inteligência artificial complementa essa análise ao transformar os resultados e documentos técnicos em explicações mais acessíveis. Ela não substitui a base oficial nem a interpretação crítica do usuário.

A escolha do Qwen local também permitiu explorar a utilização de LLMs sem depender de cobranças por requisição de uma API externa. Como o modelo roda no computador de testes, é necessário considerar o tempo de processamento e os limites da GPU. Por isso, a geração é realizada quando o usuário solicita, e os gráficos continuam disponíveis mesmo quando a IA não está sendo utilizada.


# 6 TESTES E VALIDAÇÃO DA APLICAÇÃO


## 6.1 Testes automatizados

A versão final do código foi submetida a uma bateria de testes automatizados em Python. O resultado foi de 259 testes aprovados, nenhuma falha e oito avisos de depreciação. As verificações abrangem coleta e organização de dados, cálculos estatísticos, contratos da FastAPI, validações, mensagens de erro, integração entre páginas e regras de funcionamento das funcionalidades de IA.

Os testes automatizados utilizam respostas simuladas em alguns cenários que envolvem o Qwen, porque carregar o modelo em cada teste seria desnecessário e aumentaria o consumo de recursos. Por isso, esses testes comprovam o funcionamento das regras e integrações previstas, mas não substituem a utilização efetiva da aplicação no computador.


## 6.2 Testes manuais e execução real

Além dos testes automatizados, executei a aplicação completa na minha versão local de testes e não encontrei problemas durante o uso. Essa verificação incluiu o funcionamento da interface e das funcionalidades desenvolvidas. O registro corresponde à minha experiência de teste manual, e não a uma pesquisa formal de usabilidade com diferentes usuários.

Também houve execução real do Qwen, incluindo um experimento com três versões de prompt sobre um documento coletado. O arquivo JSON desse experimento guarda as respostas e os tempos de processamento. Assim, a avaliação da solução reúne testes do código, utilização prática da interface e evidência de geração de texto pelo modelo local.


**Quadro 3 — Evidências de validação**

| Verificação | Evidência registrada |
| --- | --- |
| Testes automatizados | 259 aprovados; nenhuma falha; oito avisos de depreciação. |
| Uso da aplicação | Teste manual da aplicação completa informado pelo autor, sem problemas observados. |
| Modelo de IA | Execução real do Qwen em máquina local e resultado registrado do experimento de prompts. |
| Limite da validação | Ainda não houve pesquisa formal de usabilidade nem auditoria independente dos dados fiscais. |


## 6.3 Cuidados na interpretação dos resultados

Os testes indicam que a aplicação atende às operações verificadas, mas isso não significa que toda resposta do modelo será perfeita. Um resumo pode omitir partes importantes ou acrescentar informações que não aparecem no documento original. Por isso, mantive a identificação das fontes e a possibilidade de consultar os dados que serviram de base para a resposta.


# 7 RESULTADOS ALCANÇADOS E LIMITAÇÕES

O principal resultado foi reunir, em uma única aplicação, uma base fiscal com 27 UFs, análises interativas e uma ferramenta local de inteligência artificial. O usuário pode partir de uma pergunta simples, consultar um gráfico e obter uma explicação sem precisar interpretar diretamente arquivos fiscais ou escrever comandos de programação.

A versão apresentada ainda possui limites. O recorte fiscal abrange três funções de governo e utiliza valores nominais de despesas liquidadas. A participação percentual corresponde ao subtotal das funções selecionadas, e não ao orçamento completo. A base oficial não inclui, nesta etapa, a série populacional necessária para calcular despesas por habitante.

O projeto não mede a eficiência dos governos, não atribui resultados sociais aos valores declarados e não verifica independentemente cada informação do Siconfi. Além disso, a qualidade das respostas de IA precisa ser observada caso a caso. Esses limites não impedem o uso do dashboard para consulta e comparação, mas ajudam a definir corretamente o que a aplicação pode afirmar.


# 8 CONCLUSÃO

Com o Transparência Brasil, procurei resolver um problema prático: tornar mais simples a consulta a informações públicas que normalmente aparecem em demonstrativos técnicos. Para isso, apliquei etapas de Ciência de Dados desde a coleta até a apresentação, aproveitando a API do Siconfi, a coleta de documentos pela Web, a análise em Python e o modelo Qwen para sumarização e explicações.

O resultado final combina dados oficiais, gráficos e linguagem natural. A relação com o ODS 16 e com a governança ESG está na possibilidade de ampliar o acesso às informações e apoiar o acompanhamento das despesas públicas. Os testes automatizados e a utilização manual da aplicação indicaram funcionamento adequado no ambiente verificado. Considero que a solução atende ao objetivo principal do projeto, mantendo claras as fontes utilizadas e os limites das análises.


## ODS 16 e Governança na aplicação

Em vez de manter um documento separado de evidência, a aplicação passou a ter a categoria **Assistente IA → ODS 16 e Governança**. A mesma consulta também funciona em **Perguntar aos dados**. O sistema consulta a fonte da ONU Brasil coletada por Beautiful Soup, recupera as metas 16.6 e 16.10 e combina esse conteúdo com a descrição real do Transparência Brasil para fornecer ao Qwen um contexto verificável. A resposta mostra as fontes e deixa claro que facilitar a transparência não é o mesmo que medir o cumprimento de uma meta dos ODS. A geração efetiva da nova função deve ser conferida na instalação com o modelo local.
