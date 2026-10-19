"""Upload e download de CSV preservados do TP2, agora em página própria."""
import pandas as pd
import streamlit as st

from utils.dados import COLUNAS_GASTOS
from utils.ui import aviso_amostra, obter_amostra

st.set_page_config(page_title="Arquivos — TP3", page_icon="📁", layout="wide")
st.title("📁 Upload e download de arquivos")
aviso_amostra()

try:
    base = obter_amostra()
except (OSError, ValueError) as erro:
    st.error(str(erro))
    st.stop()

if "dados_upload" not in st.session_state:
    st.session_state["dados_upload"] = None

arquivo = st.file_uploader("Envie um CSV com até 5 MB", type="csv")
if arquivo is not None:
    try:
        if arquivo.size > 5 * 1024 * 1024:
            raise ValueError("O arquivo ultrapassa 5 MB.")
        recebido = pd.read_csv(arquivo, encoding="utf-8-sig")
        if recebido.empty:
            raise ValueError("O CSV está vazio.")
        st.session_state["dados_upload"] = recebido
    except (ValueError, UnicodeError, pd.errors.ParserError) as erro:
        st.error(f"Não foi possível ler o arquivo: {erro}")

upload = st.session_state["dados_upload"]
if upload is not None:
    st.success("CSV carregado apenas nesta sessão (não é salvo pela API).")
    st.dataframe(upload, use_container_width=True, hide_index=True)
    if set(COLUNAS_GASTOS).issubset(upload.columns):
        try:
            complemento = upload.loc[:, COLUNAS_GASTOS].copy()
            for campo in ("ano", "populacao", "valor_despesa"):
                complemento[campo] = pd.to_numeric(complemento[campo], errors="raise")
            combinado = pd.concat([base, complemento], ignore_index=True)
            st.subheader("Prévia da base complementada")
            st.caption("Dados enviados não são verificados nem alteram a amostra original.")
            st.dataframe(combinado, use_container_width=True, hide_index=True)
            st.download_button(
                "Baixar base complementada (não verificada)",
                combinado.to_csv(index=False).encode("utf-8-sig"),
                file_name="base_complementada_nao_verificada.csv", mime="text/csv",
            )
        except (ValueError, TypeError) as erro:
            st.warning(f"Colunas numéricas inválidas no arquivo enviado: {erro}")
    else:
        st.info("Para complementar a base, o CSV precisa das oito colunas da amostra original.")
    if st.button("Limpar arquivo carregado"):
        st.session_state["dados_upload"] = None
        st.rerun()

st.subheader("Baixar base original")
st.download_button(
    "Baixar amostra de gastos públicos (CSV)",
    base.to_csv(index=False).encode("utf-8-sig"),
    file_name="amostra_gastos_tp3.csv", mime="text/csv",
)
