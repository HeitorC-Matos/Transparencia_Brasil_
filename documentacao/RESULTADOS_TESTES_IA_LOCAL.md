# Integração local de IA — evidências e limites

O backend executa o modelo **Qwen3-4B-Instruct-2507** a partir de arquivos armazenados no computador. A integração utiliza FastAPI, Transformers, PyTorch e quantização NF4 via bitsandbytes. Não depende de uma API externa para gerar texto.

## Verificações do código

- Bateria de regressão da versão consolidada: **130 testes aprovados e 8 avisos de depreciação**, sem falhas, no ambiente de testes disponível.
- Modelos Pydantic verificam dados de entrada e de saída, inclusive operações não permitidas, texto vazio e resultados malformados.
- O tratamento padronizado cobre 422, 429, 500, 503 e 504, com identificador de requisição.
- Os cenários de erro de inferência são testados com um serviço simulado. Esse procedimento verifica o software, mas não demonstra, por si só, execução real na GPU.

## Execução real no Windows

O usuário confirmou a execução do modelo em um computador com **NVIDIA GeForce RTX 4060 Laptop (8 GB de VRAM) e 16 GB de RAM**. A rota `POST /processar_texto` produziu um resumo com 45 tokens de saída, em duas solicitações do mesmo texto: **72.912 ms** na primeira e **12.906 ms** na segunda. O usuário também confirmou a resposta pela interface Streamlit após as atualizações do aplicativo.

Em teste separado, o script `scripts/verificar_questao4.py` retornou **200, 200, 422 e 404** para as rotas previstas, com IDs de requisição. Esse diagnóstico HTTP não carrega o modelo.

## Limitações

O sistema foi preparado para inferência offline após o download dos pesos, mas não há registro conclusivo de teste com a conectividade física desligada e o serviço reiniciado. O valor de VRAM efetivamente ocupado durante cada geração não foi medido nesta documentação. As respostas do LLM exigem conferência de conteúdo; validação estrutural não assegura exatidão factual.

Para repetir as verificações, consulte o `README.md` e `documentacao/GUIA_LLM_LOCAL.md`.
