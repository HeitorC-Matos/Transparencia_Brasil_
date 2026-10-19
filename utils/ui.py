"""Carregamentos Streamlit compartilhados entre páginas."""
import streamlit as st
from utils.dados import ler_amostra, ler_web


@st.cache_data(ttl=60, show_spinner=False)
def obter_amostra():
    return ler_amostra()


@st.cache_data(ttl=60, show_spinner=False)
def obter_web():
    return ler_web()


def aviso_amostra():
    st.info(
        "**Base acadêmica ilustrativa:** os nove valores de gastos do TP1/TP2 "
        "foram preservados. As etiquetas Siconfi/IBGE no CSV não demonstram, "
        "por si só, a verificação desses números em bases oficiais. "
        "Os gráficos não representam totais fiscais auditados."
    )
