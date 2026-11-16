"""Preparação do corpus documental, separada da inferência com LLM."""
import json
import streamlit as st
from utils.dados import pasta_dados

st.set_page_config(page_title="Preparação para LLMs", page_icon="🤖", layout="wide")
st.title("🤖 Preparação dos dados para LLMs")
st.info("Esta página organiza os documentos sem executar um modelo de linguagem. Para resumir ou explicar textos, utilize **Assistente IA**, com Qwen local via FastAPI.")
st.markdown(
    """
Os arquivos do corpus documental são gerados pelo comando:

`python preparar_llm.py`

- **Perguntas e respostas (RAG):** recuperar trechos dos documentos Web catalogados e exibir fontes.
- **Resumos:** sintetizar o conteúdo de páginas da ONU, Siconfi e CGU.
- **Relatórios:** explicar os gráficos, sempre dizendo que a base fiscal é ilustrativa.
- **Sentimentos:** não recomendado para as tabelas numéricas ou textos institucionais atuais; exigiria textos opinativos adicionais.

As consultas fundamentadas nesses documentos deverão identificar as fontes, evitar números sem comprovação e manter os registros manuais separados.
"""
)
caminho = pasta_dados() / "llm" / "documentos.jsonl"
if caminho.exists():
    linhas = [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines() if linha.strip()]
    st.metric("Trechos preparados", len(linhas))
    st.subheader("Exemplo de documento")
    if linhas:
        st.json(linhas[0])
    st.download_button("Baixar documentos JSONL", caminho.read_bytes(),
                       file_name="documentos_transparencia.jsonl",
                       mime="application/x-ndjson")
else:
    st.warning("Arquivo ainda não preparado. Execute: python preparar_llm.py")
