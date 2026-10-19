"""Preparação de documentos para RAG e relatórios, sem executar modelo de IA."""
import json
import streamlit as st
from utils.dados import pasta_dados

st.set_page_config(page_title="Preparação para LLMs — TP3", page_icon="🤖", layout="wide")
st.title("🤖 Preparação para uso futuro de LLMs")
st.info("Nesta fase, **nenhum LLM é executado**: apenas estruturamos textos e metadados.")
st.markdown(
    """
Os arquivos para a próxima etapa são produzidos pelo comando:

`python preparar_llm.py`

- **Perguntas e respostas (RAG):** recuperar trechos dos documentos Web catalogados e exibir fontes.
- **Resumos:** sintetizar o conteúdo de páginas da ONU, Siconfi e CGU.
- **Relatórios:** explicar os gráficos, sempre dizendo que a base fiscal é ilustrativa.
- **Sentimentos:** não recomendado para as tabelas numéricas ou textos institucionais atuais; exigiria textos opinativos adicionais.

Toda resposta futura deverá identificar o documento-fonte, não inventar números e separar os registros manuais.
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
                       file_name="documentos_transparencia_tp3.jsonl",
                       mime="application/x-ndjson")
else:
    st.warning("Arquivo ainda não preparado. Execute: python preparar_llm.py")
