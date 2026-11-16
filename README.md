# Transparência Brasil

O **Transparência Brasil** é uma aplicação para explorar despesas públicas e conteúdos sobre transparência de maneira acessível. Reúne um painel interativo em Streamlit, uma API construída com FastAPI, rotinas de coleta de dados e um assistente de inteligência artificial que funciona localmente.

O projeto está associado ao **ODS 16 — Paz, Justiça e Instituições Eficazes**. Seu propósito é facilitar a compreensão das informações disponíveis, sem classificar governos como melhores ou piores e sem apresentar valores não verificados como dados oficiais.

## O que existe na aplicação

O menu do Streamlit segue esta ordem:

| Seção | O que oferece |
|---|---|
| **App** | Apresentação do projeto, indicadores gerais da amostra e acesso às funcionalidades. |
| **Gastos públicos** | Filtros e gráficos dos registros ilustrativos de São Paulo, Goiás e Bahia. |
| **Estatísticas** | Análises comparativas detalhadas da mesma amostra. |
| **Dados oficiais** | Consulta às despesas declaradas ao Siconfi por 26 estados e pelo Distrito Federal. |
| **Conteúdo da Web** | Textos de fontes institucionais, tabelas, estatísticas e nuvem de palavras. |
| **API FastAPI** | Consulta por HTTP e cadastro de registros manuais, separado da base original. |
| **Assistente IA** | Resumos e explicações produzidos pelo Qwen instalado no próprio computador. |

Os scripts de preparação de textos para IA e a antiga página de arquivos permanecem no código, mas não aparecem no menu. Isso preserva as rotinas de desenvolvimento sem sobrecarregar a interface.

## 1. Dados e fontes: duas bases fiscais diferentes

### Amostra ilustrativa de SP, GO e BA

A primeira parte utiliza `data/amostra_dados.csv`: **nove registros de 2025**, com despesas em Educação, Saúde e Segurança Pública e valores populacionais associados. É uma base de demonstração, usada em **Gastos públicos** e **Estatísticas**.

**Esses valores não foram comprovados por consultas individuais ao Siconfi ou ao IBGE.** Os nomes dessas fontes aparecem no CSV original, mas isso, por si só, não certifica os números. A amostra não representa a despesa total dos três governos. Os cadastros feitos em `POST /despesas` são armazenados separadamente em `data/registros_manuais.csv` e não modificam o arquivo original.

### Base oficial declarada ao Siconfi

A parte **Dados oficiais** é independente da amostra. Seus arquivos são:

- `data/siconfi/despesas_oficiais.csv`: base padronizada resultante da coleta;
- `data/siconfi/manifesto.json`: cobertura, critérios de extração e eventuais pendências;
- `scripts/coletar_siconfi.py`: execução e atualização da coleta;
- `documentacao/DADOS_OFICIAIS_SICONFI.md`: metodologia, regras de consistência e limitações.

O manifesto incluído nesta versão registra uma coleta **completa, com 405 registros**: 27 unidades da Federação × 5 exercícios (2021 a 2025) × 3 funções de governo, sem combinações pendentes. A estrutura foi conferida quanto a quantidade de linhas, UFs, exercícios, funções e ausência de duplicidades por UF/ano/função.

A fonte é o **RREO — Anexo 02 (Despesas por Função/Subfunção)** do Siconfi/Tesouro Nacional. Para cada exercício, o programa seleciona o **6º bimestre**, a coluna **despesas liquidadas até o bimestre (d)**, as linhas sintéticas de **Segurança Pública (06), Saúde (10) e Educação (12)**, excluindo o quadro intraorçamentário. Os valores são nominais e representam declarações dos entes ao Siconfi, **não contas auditadas por esta aplicação**.

O painel permite comparar valores por UF, observar séries anuais, consultar agregados regionais quando há cobertura suficiente e acessar a URL vinculada a cada extração. A coleta respeita o intervalo entre chamadas e mantém um cache bruto local. **Os arquivos brutos e os históricos de coleta não são publicados no GitHub**; a base consolidada, o manifesto e o código da coleta permanecem no projeto.

A seleção de 405 registros atende ao escopo atual, mas não equivale à totalidade das despesas de cada governo: somente três funções foram extraídas. Não há, por enquanto, vínculo validado com uma série populacional oficial do IBGE nem deflacionamento pelo IPCA; portanto, a base oficial não oferece despesas per capita ou valores corrigidos pela inflação. A validação automática de estrutura também **não substitui o confronto amostral com os demonstrativos originais**. Essas melhorias ficam como possibilidades de evolução.

## 2. Estatísticas ampliadas para três estados

A página **Estatísticas** trabalha **apenas com a amostra ilustrativa de 2025**, sem misturar os dados oficiais das 27 UFs ou os cadastros manuais. Os cálculos estão em `utils/estatisticas_amostra.py`, e os testes específicos em `tests/test_estatisticas_amostra.py`.

As análises estão organizadas em cinco grupos:

1. **Distribuição das despesas:** participação de Educação, Saúde e Segurança Pública na soma das três funções de cada estado, com gráficos e comparação de percentuais.
2. **Por habitante e rankings:** valores por habitante para cada função e ordenação dos estados por montante ou valor per capita.
3. **Comparação entre dois estados:** diferenças absolutas e percentuais para a função selecionada, inclusive por habitante.
4. **Perfil de um estado:** quadro individual com despesas, população e função de maior valor dentro da amostra.
5. **Matriz e estatísticas descritivas:** cruzamento estado × função, média, mediana, valores mínimo e máximo e amplitude.

A leitura dos percentuais exige um cuidado: o denominador é **a soma das três funções presentes na amostra**, não o orçamento total de cada estado. Um ranking por despesa também não mede eficiência, qualidade dos serviços ou desempenho da gestão. Como só existe o exercício de 2025, a página não faz inferência temporal ou projeções.

## 3. Conteúdo da Web e preparação de textos

O arquivo `coleta_web.py` usa **Requests e Beautiful Soup** para obter textos institucionais da ONU (ODS 16), do Tesouro Nacional (Siconfi) e da CGU. A coleta com navegador é executada separadamente por `coleta_selenium.py`, sobre uma página governamental de transparência ativa. Seus resultados foram armazenados em `data/conteudo_web.csv/.txt` e `data/conteudo_selenium.csv/.txt`.

Os arquivos fornecidos contêm **três fontes Beautiful Soup e uma fonte Selenium**. O CSV de Selenium registra uma coleta efetiva com o método `selenium+chromium`; os testes automatizados do coletor, por sua vez, utilizam um navegador simulado e não devem ser confundidos com essa execução real.

Para organizar os textos para uso posterior, execute:

```powershell
python preparar_llm.py
```

O corpus versionado em `data/llm/documentos.jsonl` contém **16 fragmentos**: sete provenientes das quatro fontes Web e nove descrições da amostra ilustrativa. O manifesto respectivo registra que essa preparação **não executa um LLM**. Não existe, nesta versão, um mecanismo RAG que consulte automaticamente todo esse corpus para responder perguntas abertas.

## 4. Inteligência artificial local — Qwen

O assistente utiliza **Qwen3-4B-Instruct-2507**, da família Qwen, disponibilizado no Hugging Face. O modelo foi selecionado por sua capacidade de seguir instruções e produzir respostas em linguagem natural, pelo suporte a português e pela possibilidade de executar sem uma API de inferência externa.

O serviço em `services/llm_service.py` carrega o modelo a partir da pasta local `models/qwen3-4b-instruct-2507/`, com **Transformers, PyTorch CUDA, Accelerate e bitsandbytes** e quantização **NF4 de 4 bits**. O carregamento é realizado na primeira solicitação, e uma geração por vez utiliza a GPU. O download dos pesos é uma etapa separada: a FastAPI não faz download automático nem envia os textos para um serviço remoto de LLM. Após baixar os arquivos, a inferência foi desenvolvida para funcionar sem acesso à Internet.

A integração foi testada no computador de desenvolvimento com **NVIDIA GeForce RTX 4060 Laptop (8 GB de VRAM) e 16 GB de RAM**. Foram obtidas respostas reais por `POST /processar_texto` e pela página Assistente IA. O tempo relatado para a primeira solicitação foi aproximadamente 72,9 s e, com o modelo já carregado, 12,9 s no mesmo exemplo. Essas medições são específicas daquele ambiente; **o teste com a conexão física à Internet desligada ainda não foi documentado**.

A rota `POST /processar_texto` aceita `resumo` e `explicacao`. A página **Dados oficiais** também permite solicitar uma explicação dos registros selecionados, que são fornecidos explicitamente no texto enviado ao Qwen. O sistema não delega cálculos fiscais ao modelo. Como qualquer modelo de linguagem, o Qwen pode produzir interpretações imprecisas; por isso, as respostas trazem aviso para conferir os dados e as fontes.

### Modelos de resposta e erros da API

A API usa **Pydantic v2 e `response_model` do FastAPI** para validar os campos das entradas e das saídas: operação, texto, resultado, identificação do modelo, contagem de tokens, tempo de processamento e indicadores de execução local. Respostas vazias ou com tipos incompatíveis não são aceitas como resultados bem-sucedidos.

O tratamento de exceções em `api/erros.py` padroniza mensagens e fornece `X-Request-ID` para localizar as solicitações nos logs. Os principais códigos são:

| HTTP | Quando pode ocorrer |
|---|---|
| `422` | Texto, operação ou outro campo inválido. |
| `429` | O modelo já está processando outra requisição; inclui `Retry-After`. |
| `500` | Erro interno ou resposta fora do contrato esperado. |
| `503` | Qwen indisponível, dependências/GPU inadequadas ou serviço fiscal indisponível. |
| `504` | Tempo máximo de geração excedido. |
| `404` | Rota não encontrada. |

O Streamlit transforma esses retornos em orientações compreensíveis. O limite de geração é cooperativo, de **180 segundos por padrão**, configurável por `TP4_LLM_MAX_SECONDS`; não garante interrupção instantânea de operações CUDA. O limite de uma geração simultânea foi mantido para proteger a memória de vídeo.

## 5. Instalação e execução no Windows

Recomendado: **Python 3.11**, ambiente virtual próprio e, para a IA, uma GPU NVIDIA com suporte a CUDA e memória suficiente. As rotas de consultas e os gráficos também funcionam sem o Qwen instalado, mas o assistente precisa dos pesos locais.

Na pasta principal do projeto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Se o PowerShell bloquear a ativação, pode-se usar `Set-ExecutionPolicy -Scope Process RemoteSigned` apenas nessa sessão ou executar os comandos com `.\.venv\Scripts\python.exe` sem ativar o ambiente.

**Aplicação sem IA:**

```powershell
python -m pip install -r requirements.txt
```

**Aplicação com Qwen local:** instale primeiro uma versão do PyTorch compatível com a GPU, o driver e o CUDA disponibilizado pelo projeto. A configuração utilizada nos testes do Windows foi:

```powershell
python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r requirements-llm.txt
python scripts/diagnostico_gpu.py
python scripts/baixar_modelo.py
```

O `requirements-llm.txt` já inclui o `requirements.txt`. O download do Qwen é necessário **somente na primeira instalação** e ficará fora do Git. Confira [o guia detalhado de instalação](documentacao/GUIA_LLM_LOCAL.md) para soluções de incompatibilidade e requisitos locais.

Em **dois terminais**, no mesmo ambiente e na raiz do projeto:

**Terminal 1 — FastAPI**

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Terminal 2 — Streamlit**

```powershell
python -m streamlit run app.py
```

Abra a interface em **http://localhost:8501** e a documentação da API em **http://127.0.0.1:8000/docs**. Os processos devem permanecer abertos. A variável `TP3_API_URL` permite apontar o Streamlit para outra URL da API; por padrão, ela usa a porta 8000 no próprio computador. Não utilize vários workers da API ao carregar o Qwen em uma única GPU de 8 GB.

## 6. Consultas e atualização das fontes

Principais rotas documentadas em `/docs`:

| Endpoint | Utilização |
|---|---|
| `GET /health` | Estado geral da API. |
| `GET /despesas` e `POST /despesas` | Consulta e cadastro manual de registros ilustrativos. |
| `GET /estatisticas` | Totais calculados sobre a origem selecionada. |
| `GET /conteudo-web` | Textos institucionais extraídos. |
| `GET /dados-oficiais/status` | Cobertura da base do Siconfi e eventuais pendências. |
| `GET /dados-oficiais` | Consulta de despesas oficiais por UF, ano e função. |
| `GET /dados-oficiais/serie` | Evolução nominal por UF e função. |
| `GET /dados-oficiais/regioes` | Agregação regional condicionada à cobertura. |
| `GET /ia/health` | Estado do Qwen, sem carregá-lo só para o diagnóstico. |
| `POST /processar_texto` | Resumo ou explicação por IA local. |

Para **repetir ou atualizar** as coletas, quando necessário:

```powershell
python coleta_web.py
python coleta_selenium.py
python preparar_llm.py
python scripts/coletar_siconfi.py --ufs SP GO BA
python scripts/coletar_siconfi.py --todas
```

Os coletores Web e Siconfi precisam de Internet, e o Selenium precisa de Chrome/Chromium e driver compatível. A execução de `preparar_llm.py` deve ser feita após alterações nas fontes textuais. Para atualizar declarações fiscais previamente armazenadas, utilize `python scripts/coletar_siconfi.py --todas --atualizar` e verifique o novo manifesto. **Não é obrigatório repetir a coleta fiscal para abrir o painel:** a base consolidada e seu manifesto já acompanham este repositório.

## 7. Testes e verificações

```powershell
python -m pytest -q
```

**Na versão consolidada deste repositório, 130 testes automatizados passaram, com 8 avisos de depreciação e nenhuma falha**, no ambiente de verificação do código. Eles abrangem o cliente HTTP, a API, os modelos Pydantic, as estatísticas da amostra, o tratamento de erros, o menu, a extração de conteúdo e a lógica do coletor Siconfi com respostas simuladas. Os testes de software não substituem a conferência contábil das declarações nem uma medição real da GPU.

Com a FastAPI ligada, também é possível executar:

```powershell
python scripts/verificar_questao4.py
```

Esse teste consulta rotas de diagnóstico e testa erros HTTP **sem carregar o Qwen**. A geração efetiva pela API e a navegação no Streamlit foram confirmadas pelo usuário no Windows; os resultados detalhados e as limitações estão em [Resultados da IA local](documentacao/RESULTADOS_TESTES_IA_LOCAL.md) e no [Relatório de testes](documentacao/RELATORIO_TESTES.md).

## 8. Organização do repositório e publicação

```text
Transparencia_Brasil/
├── app.py                         # Entrada e menu Streamlit
├── pages/                        # Páginas da interface
├── api/                          # Rotas, modelos de resposta e erros
├── services/                     # Inferência local e integração fiscal
├── utils/                        # Cliente HTTP, dados e estatísticas
├── scripts/                      # Download, diagnóstico e testes locais
├── data/
│   ├── amostra_dados.csv          # 9 registros ilustrativos
│   ├── conteudo_web.csv           # Extração Beautiful Soup
│   ├── conteudo_selenium.csv      # Extração Selenium
│   ├── llm/                      # 16 fragmentos preparados
│   └── siconfi/                  # 405 registros e manifesto da coleta
├── tests/                        # Testes automatizados
├── documentacao/                 # Metodologia, relatórios e guias
├── requirements.txt
├── requirements-llm.txt
├── DECLARACAO_USO_IA.txt
└── README.md
```

A distribuição para o GitHub inclui o **código, a documentação, a base fiscal consolidada e os arquivos de exemplo**, mas exclui a pasta `models/`, os ambientes virtuais `.venv/`, caches brutos do Siconfi, históricos locais, backups e `data/registros_manuais.csv`. Os arquivos ignorados são reproduzíveis ou pertencem à instalação local. A chave de acesso ou o login para serviços externos **não são necessários** para o funcionamento básico da API local.

Para publicar em um repositório Git já clonado, copie **o conteúdo da pasta extraída** para a raiz do clone, preservando `.git`, e execute `git status`, `git add .`, `git commit -m "Atualiza aplicação, IA local e dados fiscais"` e `git push`. Caso utilize a interface Web do GitHub, envie os **arquivos e subpastas extraídos**, não o arquivo ZIP isolado: o GitHub não descompacta automaticamente um ZIP enviado como arquivo do repositório.

**Segurança:** o cadastro manual não possui autenticação; mantenha a API ligada somente a `127.0.0.1`, não a exponha publicamente sem autenticação e medidas adicionais de proteção.

## Histórico das entregas acadêmicas

A proposta original das primeiras etapas (TP1 e TP2) definiu o problema de negócio e estruturou a amostra ilustrativa para São Paulo, Goiás e Bahia. O TP3 acrescentou a extração Web com Beautiful Soup e Selenium, a integração HTTP entre Streamlit e FastAPI, os testes e o corpus preparado para IA.

No **TP4**, foram documentadas e implementadas as quatro frentes: **(1)** seleção e justificativa do Qwen3-4B-Instruct-2507, **(2)** inferência local integrada à FastAPI, **(3)** `response_model` e validação com Pydantic, e **(4)** tratamento de exceções com códigos HTTP específicos. Depois dessas etapas, foram ampliados o painel de Estatísticas e o módulo independente de Dados Oficiais para consulta e possível evolução futura da base nacional.

O uso de ferramentas de IA está declarado em [`DECLARACAO_USO_IA.txt`](DECLARACAO_USO_IA.txt). Os materiais específicos de cada etapa e os critérios de coleta estão disponíveis em `documentacao/`. **As referências acadêmicas permanecem na documentação, não nos títulos nem no menu da aplicação.**
