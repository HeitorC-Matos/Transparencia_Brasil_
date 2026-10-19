"""Página inicial do TP3; as outras páginas aparecem no menu lateral."""
import streamlit as st
from utils.ui import aviso_amostra, obter_amostra, obter_web
from utils.api_client import verificar_api

st.set_page_config(page_title="Transparência Brasil — TP3", page_icon="📊", layout="wide")
st.title("📊 Transparência Brasil — TP3")
st.write(
    "Projeto acadêmico de visualização de despesas estaduais de **São Paulo, "
    "Goiás e Bahia**, associado ao **ODS 16 — Paz, Justiça e Instituições Eficazes**."
)
st.sidebar.success("Selecione uma das páginas acima para explorar o projeto.")
st.sidebar.caption("FastAPI: " + ("online ✓" if verificar_api() else "offline — inicie uvicorn"))

try:
    despesas = obter_amostra()
    web = obter_web()
except (OSError, ValueError) as erro:
    st.error(f"Não foi possível carregar a base: {erro}")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Registros na amostra", len(despesas))
col2.metric("Estados comparados", despesas["sigla"].nunique())
col3.metric("Páginas Web catalogadas", len(web))

aviso_amostra()
st.subheader("O que mudou no TP3?")
st.markdown(
    """
- **Gastos públicos:** filtros e gráficos dedicados para comparação por estado e função.
- **Conteúdo da Web:** fontes do TP2 e CGU, com coletor Selenium opcional, estatísticas e nuvem.
- **Arquivos:** upload e download de CSV, sem alterar a amostra original.
- **Estatísticas:** totais ilustrativos e valores por habitante.
- **API FastAPI integrada:** gráficos e consultas GET por HTTP e formulário POST diretamente na interface.
- **Preparação para IA:** textos em JSONL, com referência às fontes, para uso posterior em LLMs.
"""
)
st.caption("Use o menu de navegação na barra lateral para abrir cada página.")
