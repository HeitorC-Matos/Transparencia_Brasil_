# Execução local do Qwen com FastAPI

## 1. Objetivo e arquitetura

O projeto passa a disponibilizar `POST /processar_texto` para resumir e explicar textos. O caminho de processamento é **Streamlit → cliente HTTP → FastAPI → Transformers/PyTorch → Qwen3-4B-Instruct-2507 armazenado no disco → resposta JSON**. A chamada HTTP ocorre exclusivamente entre programas no próprio computador (`127.0.0.1`). Nenhum serviço externo de geração de texto é utilizado.

O modelo foi selecionado considerando desempenho, memória disponível e compatibilidade local. A **justificativa técnica completa**, com comparação a BERT/T5 e modelos maiores, parâmetros, licença, disponibilidade no Hugging Face, VRAM e latências medidas, encontra-se na seção **“Por que escolhemos o Qwen3-4B-Instruct-2507 em vez de outro modelo?” do README**. A máquina de referência tem **16 GB de RAM e NVIDIA RTX 4060 Laptop com 8188 MiB de VRAM**. Por isso, usamos quantização bitsandbytes NF4 de 4 bits, computação float16, máximo de 2.048 tokens totais de entrada e até 384 novos tokens por solicitação, por padrão. O uso efetivo de RAM/VRAM e a latência **devem ser medidos localmente**: não há resultados inventados no relatório. Não recomendamos habilitar múltiplos processos workers de Uvicorn, pois cada um poderia carregar sua própria cópia do modelo.

O modelo é carregado **sob demanda, uma vez por processo**. Seu primeiro processamento demora mais devido à leitura dos pesos. Os endpoints legados seguem disponíveis mesmo que o LLM não esteja instalado. O serviço não faz download automático: a única rotina que usa internet para baixar pesos é `scripts/baixar_modelo.py`, executada separadamente. `local_files_only=True` e `HF_HUB_OFFLINE=1` impedem consultas ao Hub durante a inferência.

## 2. Preparação no Windows (PowerShell)

Use Python **3.11** ou **3.12**. Na pasta raiz do projeto (onde está `api/`), abra PowerShell:

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
nvidia-smi
```

Se a ativação for bloqueada, execute `Set-ExecutionPolicy -Scope Process RemoteSigned` e repita a ativação. Se o comando `py -3.11` não funcionar, instale Python 3.11 ou utilize `py -3.12` nas duas primeiras linhas. Não misture dependências do novo ambiente virtual com outros projetos.

Instale **PyTorch com CUDA**. Como opção com suporte oficial Windows/CUDA 12.6 (exige driver NVIDIA compatível):

```powershell
python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r requirements-llm.txt
python scripts/diagnostico_gpu.py
```

Caso o driver NVIDIA não seja compatível com CUDA 12.6, atualize o driver pelo site NVIDIA antes da instalação; a disponibilidade de versões deve ser conferida no [seletor oficial de instalação do PyTorch](https://pytorch.org/get-started/locally/) ou no [histórico de builds](https://pytorch.org/get-started/previous-versions/). O `nvidia-smi` mostra dados do driver, não a versão do toolkit de desenvolvimento instalada. **O toolkit CUDA completo não é necessário** para usar as rodas CUDA pré-compiladas do PyTorch.

O diagnóstico deve informar `CUDA disponível: True`, reconhecer a RTX 4060 e mostrar versões instaladas de Transformers, Accelerate e bitsandbytes. **Não prossiga para baixar pesos se o CUDA estiver indisponível**, para evitar erros difíceis de diagnosticar.

## 3. Download único do modelo (com internet)

```powershell
python scripts/baixar_modelo.py
```

O script baixa os arquivos do repositório oficial `Qwen/Qwen3-4B-Instruct-2507` para `models/qwen3-4b-instruct-2507/`. Reserve vários GB de espaço em disco e mantenha a conexão até o término. Esse diretório está no `.gitignore`; não publique os pesos no GitHub. O formato de armazenamento original ocupa mais espaço que a versão carregada em 4 bits na GPU.

Para conferir apenas o estado dos arquivos sem iniciar o modelo:

```powershell
python scripts/diagnostico_gpu.py
```

## 4. Subir a aplicação e validar a inferência real

**Terminal 1**, na raiz e com `.venv` ativado:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Terminal 2**, também com o ambiente ativado:

```powershell
python scripts/teste_llm_http_real.py
```

O primeiro `POST` carrega o Qwen na RTX 4060. O script faz uma requisição HTTP verdadeira e verifica o status 200, a identificação do modelo, o texto produzido e a quantidade de tokens. Se falhar, retorna código diferente de zero e mostra a mensagem de erro. Uma resposta de teste simulado **não substitui essa prova**.

**Terminal 3** (ou depois de terminar o teste), para a interface:

```powershell
python -m streamlit run app.py
```

No navegador, use http://127.0.0.1:8501 e abra **Assistente IA**. Cole um texto, selecione resumo/explicação e processe. A rota também pode ser testada na documentação interativa `http://127.0.0.1:8000/docs`.

Exemplo opcional em PowerShell:

```powershell
$corpo = @{
  texto = "Os valores do projeto são ilustrativos e não equivalem a estatísticas oficiais."
  operacao = "resumo"
  max_novos_tokens = 128
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/processar_texto" -Method Post -ContentType "application/json; charset=utf-8" -Body $corpo
```

## 5. Verificação do funcionamento totalmente offline

1. **Conclua primeiro o download e um teste real bem-sucedido.**
2. Encerre os programas, desconecte a internet (ou bloqueie acesso à rede externa) e reinicie a API com o mesmo comando.
3. Abra a interface ou execute `python scripts/teste_llm_http_real.py` novamente.
4. Confirme que a API gera respostas normalmente, e que nenhum arquivo do modelo precisou ser baixado.

Não é necessário desligar a rede local: Streamlit e FastAPI conversam apenas com `127.0.0.1`. O modo de execução sempre usa arquivos locais, mesmo quando a máquina está conectada à internet.

## 6. Contratos de uso

`GET /health`: retorna o estado da API (legado).

`GET /ia/health`: retorna o estado do LLM (`arquivos_ausentes`, `nao_carregado`, `carregado` ou `erro_carregamento`). A consulta não carrega pesos.

`POST /processar_texto`: corpo JSON obrigatório:

```json
{
  "texto": "Texto a ser resumido ou explicado.",
  "operacao": "resumo",
  "max_novos_tokens": 256
}
```

Operações aceitas: `resumo` e `explicacao`. O campo `texto` deve conter de 1 a 12.000 caracteres e caber no limite de 2.048 tokens **após** a aplicação do prompt e das instruções. `max_novos_tokens` aceita 32 a 512.

Resposta de sucesso, com valores ilustrativos:

```json
{
  "operacao": "resumo",
  "texto_original": "Texto a ser resumido ou explicado.",
  "resultado": "Exemplo de resposta produzida pelo modelo.",
  "modelo": "Qwen/Qwen3-4B-Instruct-2507",
  "execucao_local": true,
  "tokens_entrada": 70,
  "tokens_saida": 40,
  "tempo_processamento_ms": 1500,
  "aviso": "Resultado gerado por IA local; verifique as informações antes de utilizá-las."
}
```

Esses números **não são medições**. A API também responde 422 para dados inválidos ou prompt longo, 503 para modelo indisponível, 429 para uso simultâneo e 500 para erro inesperado. O tratamento detalhado de erros e a validação dos contratos serão ampliados em atualizações específicas.

## 7. Testes, limites e próximas etapas

Teste de regressão e contrato, sem carregar pesos:

```powershell
python -m pytest -q
```

Na versão consolidada, **184 testes automatizados passaram, com oito avisos de depreciação e nenhuma falha**. Os testes de serviços e erros da IA utilizam inferência simulada para verificar fluxos e contratos; por si só, **não atestam a geração real na GPU**. Essa execução foi confirmada separadamente pelo usuário no Windows.

Na execução local informada pelo usuário, duas respostas da API registraram 72.912 ms (primeiro carregamento e geração) e 12.906 ms (segunda geração). A GPU foi identificada em uso pelo Python e o Streamlit exibiu a resposta. A execução com a internet desconectada e uma medição detalhada da VRAM ainda não foram confirmadas. Os valores foram relatados pelo usuário, não reproduzidos neste ambiente. A busca semântica RAG sobre os 16 fragmentos ainda não foi implementada. A nova sumarização permite selecionar diretamente os textos institucionais já coletados, enquanto o endpoint legado `/processar_texto` continua processando **o texto recebido**, sem afirmar que fez busca documental.

A qualidade da geração pode variar e respostas podem conter erros. Não confunda a amostra ilustrativa com os dados fiscais declarados ao Siconfi: são bases independentes e têm limites de interpretação diferentes. A API deve permanecer ligada a `127.0.0.1`: as rotas de cadastro antigas e as novas rotas de IA não foram projetadas para exposição pública sem autenticação e controles adicionais.

### Referências técnicas

- Modelo oficial Qwen: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Execução offline em Transformers: https://huggingface.co/docs/transformers/installation
- Bitsandbytes, quantização em 4 bits: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- Instalação do PyTorch/CUDA: https://pytorch.org/get-started/locally/
- Versões do PyTorch (Windows/CUDA): https://pytorch.org/get-started/previous-versions/
