"""Análises populadas por GET /despesas e GET /estatisticas da FastAPI."""
import streamlit as st
from utils.analises import formatar_reais, gasto_por_habitante
from utils.api_client import APIIndisponivel, consultar_despesas, consultar_estatisticas
from utils.ui import aviso_amostra, obter_amostra

st.set_page_config(page_title="Estatísticas — TP3", page_icon="📈", layout="wide")
st.title("📈 Estatísticas da amostra")
aviso_amostra()

try:
    df = consultar_despesas(origem="amostra_academica")
    resumo = consultar_estatisticas(origem="amostra_academica")
    st.success("Dados obtidos por HTTP: GET /despesas e GET /estatisticas.")
    st.caption("A API retorna um resumo geral; o filtro por ano é aplicado aos registros consultados.")
except (APIIndisponivel, OSError, ValueError) as erro:
    st.warning(f"API indisponível ({erro}). Usando amostra local temporariamente.")
    df = obter_amostra()
    resumo = None

if df.empty:
    st.info("Nenhum registro encontrado.")
    st.stop()

ano = st.selectbox("Ano de referência", sorted(df["ano"].unique(), reverse=True))
filtrado = df[df["ano"] == ano].copy()

col1, col2, col3 = st.columns(3)
col1.metric("Valor total da amostra", formatar_reais(filtrado["valor_despesa"].sum()))
col2.metric("Funções", filtrado["funcao"].nunique())
col3.metric("Registros", len(filtrado))
if resumo is not None:
    with st.expander("Resumo geral retornado por GET /estatisticas"):
        st.json(resumo)

st.subheader("Gastos por estado e função")
quadro = filtrado.pivot_table(
    index="estado", columns="funcao", values="valor_despesa", aggfunc="sum", fill_value=0
)
st.bar_chart(quadro)
st.dataframe(quadro.reset_index(), use_container_width=True, hide_index=True)

st.subheader("Gasto total por habitante")
st.caption("A população é considerada uma vez por estado/ano, sem somar linhas repetidas.")
por_pessoa = gasto_por_habitante(filtrado)
st.bar_chart(por_pessoa.set_index("estado")[["valor_por_habitante"]])
st.dataframe(
    por_pessoa[["estado", "total", "populacao", "valor_por_habitante"]],
    use_container_width=True, hide_index=True,
)
