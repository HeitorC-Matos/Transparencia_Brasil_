# Perguntas em linguagem natural sobre dados fiscais oficiais

## Objetivo e separação de responsabilidades

A aba **Perguntar aos dados**, no Assistente IA, permite consultar os registros de despesas liquidadas declarados ao Siconfi para 27 UFs e exercícios de 2021 a 2025. A funcionalidade é **complementar** à Tarefa 2 (sumarização de documentos) e não substitui os recursos existentes.

- A **interpretação de linguagem natural** usa um reconhecedor **delimitado e determinístico** de intenções, UFs, funções e anos. Não é um agente autônomo nem responde qualquer pergunta aberta.
- O **Python** valida a cobertura e produz rankings, comparações, séries, consultas individuais e percentuais usando `decimal.Decimal`. A saída calculada constitui a resposta principal.
- O **Qwen**, quando habilitado, recebe **somente o resultado calculado e os critérios**, não a pergunta original. Ele produz uma explicação complementar, claramente identificada. O modelo **não decide valores nem reescreve a resposta principal**.
- As fontes utilizadas e os registros efetivamente consultados são retornados pela API e exibidos no Streamlit. O sistema não acessa a Internet para responder.

## Dados e critérios

Base: `data/siconfi/despesas_oficiais.csv`, mantida separada de `data/amostra_dados.csv`. Dados declaratórios do Siconfi, **RREO Anexo 02, sexto bimestre, despesas liquidadas acumuladas**, exceto intraorçamentárias, no nível dos governos estaduais e do Distrito Federal. **Não inclui governos municipais**. A soma das três funções (Educação, Saúde e Segurança Pública) **não corresponde ao orçamento total**. Os valores são nominais, sem correção inflacionária; não há população integrada e, portanto, não existe indicador per capita nesta ferramenta.

A palavra *investiu*, usada informalmente pelo cidadão, é interpretada como *despesa liquidada na função*. A resposta adverte que essa métrica não é necessariamente investimento de capital. A ferramenta não afirma que os dados tenham sido auditados independentemente.

Consultas implementadas:

1. **Ranking nacional (27 UFs)** — maior/menor valor da função em um ano; exige cobertura das 27 UFs para evitar classificar somente os estados com dados presentes.
2. **Consulta de UF** — valor liquidado de uma função em um ano.
3. **Comparação de duas UFs** — valores, diferença nominal absoluta e diferença percentual calculada sobre a UF de menor valor; se a base é zero, não inventa percentual.
4. **Série histórica** — de 2021 a 2025, ou entre dois anos explicitamente indicados; não confunde variação nominal com real e rejeita anos ausentes.
5. **Composição percentual** — uma ou três funções como percentual do **subtotal dessas três funções**, e não do orçamento geral. Verifica previamente os três registros.

Se a pergunta não indicar exercício, o `ano_referencia` selecionado no Streamlit (2025 por padrão) é empregado e explicado. A API rejeita perguntas fora do escopo com HTTP 422 (ex.: por habitante, orçamento total, anos fora de 2021–2025, consultas sem função identificável) e dados oficiais indisponíveis com HTTP 503. Não se imputa zero a registros faltantes. **Não há SQL gerado por IA**.

## Arquitetura e arquivos

| Camada | Arquivo / rota | Papel |
|---|---|---|
| Interpretação e cálculo | `services/perguntas_fiscais.py` | Reconhece cinco operações e executa cálculos com `Decimal` sobre a base validada |
| Base fiscal | `services/consulta_oficial.py` | Carrega e valida os registros do Siconfi |
| Contratos | `api/schemas/perguntas.py` | Valida pergunta, ano, flag Qwen e estrutura de saída |
| Backend | `api/routes/perguntas.py` | `POST /ia/perguntar_dados` com execução Qwen opcional e fallback numérico |
| FastAPI | `api/main.py` | Registra rota nova sem remover as anteriores |
| Cliente HTTP | `utils/api_client.py` | Chamada única à API, com timeout e verificação do formato |
| Streamlit | `pages/7_Assistente_IA.py` | Nova aba Perguntar aos dados; preserva outras três abas |

### Exemplo de requisição

```json
{
  "pergunta": "Qual foi o estado que mais gastou com Educação em 2025?",
  "ano_referencia": 2025,
  "usar_qwen": true,
  "max_novos_tokens": 192
}
```

Resposta: `tipo`, `pergunta_interpretada`, `resposta_calculada`, lista `dados` com UF/ano/função/valor/fonte, `fontes`, `criterio`, `observacoes`, `qwen_executado` e, se disponível, `explicacao_ia`, `modelo` e métricas de tokens/tempo. **Se a GPU não estiver disponível, a resposta exata calculada pelo Python continua sendo devolvida**, com aviso explícito de que o complemento do Qwen não foi executado.

## Avaliação e limites

Testes automatizados verificam as cinco intenções, aliases de UF, reconhecimento do ano, exatidão do `Decimal`, cobertura das 27 UFs, lacunas, indicadores fora do escopo, contrato FastAPI, cliente HTTP e geração simulada do Qwen. O resultado consolidado deste pacote é **221 testes aprovados com 8 avisos de depreciação**, no ambiente de verificação sem modelo/GPU. **A geração efetiva da nova rota com Qwen precisa de execução no computador local**. Não foi realizada avaliação independente da correção contábil de cada valor publicado pelo Siconfi.

Para testar, execute `python -m pytest -q` e, com FastAPI/Streamlit em execução, formule as perguntas de exemplo exibidas na aba. Teste uma primeira vez **sem** marcar a explicação por IA para validar a consulta e depois **com** a opção ativa, para validar o Qwen local.


## Perguntas institucionais sobre ODS 16 e Governança

A rota `/ia/perguntar_dados` também reconhece perguntas sobre o Transparência Brasil, ODS 16 (metas 16.6 e 16.10) e Governança ESG. Essas perguntas usam documentação do projeto e o texto da ONU coletado pela aplicação, em vez de cálculos fiscais. A resposta tem `tipo="ods16"`, lista vazia de registros fiscais, fontes documentais e, quando solicitado, explicação complementar do Qwen. A interface oferece ainda uma categoria própria **ODS 16 e Governança**, conforme [`ODS16_E_GOVERNANCA_INTERATIVA.md`](ODS16_E_GOVERNANCA_INTERATIVA.md).
