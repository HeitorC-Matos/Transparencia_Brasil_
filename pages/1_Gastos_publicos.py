"""Comparação de despesas obtidas de /despesas da FastAPI via HTTP."""
import streamlit as st
from utils.analises import formatar_reais
from utils.api_client import APIIndisponivel, consultar_despesas
from utils.ui import aviso_amostra, obter_amostra

st.set_page_config(page_title="Gastos públicos — TP3", page_icon="💰", layout="wide")
st.title("💰 Gastos públicos por estado")
aviso_amostra()

try:
    df = consultar_despesas(origem="amostra_academica")
    st.success("Dados consultados na FastAPI: GET /despesas (HTTP).")
except (APIIndisponivel, OSError, ValueError) as erro:
    st.warning(f"FastAPI indisponível ({erro}). Exibindo amostra local somente para visualização.")
    try:
        df = obter_amostra()
    except (OSError, ValueError) as erro_local:
        st.error(str(erro_local))
        st.stop()

if df.empty:
    st.info("A API não retornou registros para a amostra.")
    st.stop()

estados = st.multiselect("Selecione os estados", sorted(df["estado"].unique()),
                        default=sorted(df["estado"].unique()))
funcao = st.selectbox("Função de despesa", sorted(df["funcao"].unique()))
anos = sorted(int(ano) for ano in df["ano"].unique())
ano = st.selectbox("Ano", anos, index=len(anos) - 1)
filtrado = df.loc[
    df["estado"].isin(estados) & df["funcao"].eq(funcao) & df["ano"].eq(ano)
].copy()

if filtrado.empty:
    st.warning("Nenhum dado encontrado para esses filtros.")
else:
    col1, col2 = st.columns(2)
    col1.metric("Soma da seleção (ilustrativa)", formatar_reais(filtrado["valor_despesa"].sum()))
    col2.metric("Estados na seleção", filtrado["estado"].nunique())
    st.subheader("Comparação por estado")
    st.bar_chart(filtrado.set_index("estado")[["valor_despesa"]])
    st.subheader("Registros filtrados")
    tabela = filtrado[["estado", "sigla", "ano", "funcao", "valor_despesa", "populacao"]].copy()
    tabela["valor_despesa"] = tabela["valor_despesa"].map(formatar_reais)
    st.dataframe(tabela, use_container_width=True, hide_index=True)
