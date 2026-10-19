"""Página interativa que executa GET e POST reais na FastAPI."""
import streamlit as st
from utils.api_client import (
    APIIndisponivel, base_url, cadastrar_despesa, consultar_despesas,
    consultar_estatisticas, verificar_api,
)
from utils.dados import ESTADOS, FUNCOES

st.set_page_config(page_title="API FastAPI — TP3", page_icon="🔌", layout="wide")
st.title("🔌 Integração Streamlit ↔ FastAPI")
st.caption("Todas as consultas e cadastros nesta página são requisições HTTP à API personalizada.")
st.code("uvicorn api.main:app --reload", language="bash")
st.write(f"Servidor configurado: `{base_url()}` — documentação: `{base_url()}/docs`.")
st.warning("A API não possui login. Utilize POST apenas em ambiente local de estudo.")

if not verificar_api():
    st.error("A FastAPI está desligada ou inacessível. Inicie-a no segundo terminal para habilitar as consultas e o cadastro.")
    st.stop()
st.success("FastAPI online: GET /health retornou status ok.")

st.subheader("Consultar dados: GET /despesas")
col1, col2, col3 = st.columns(3)
uf = col1.selectbox("UF", ["Todas", *ESTADOS], index=0)
origem = col2.selectbox("Origem", ["amostra_academica", "manual"])
funcao = col3.selectbox("Função", ["Todas", *FUNCOES])
try:
    filtrados = consultar_despesas(
        sigla=None if uf == "Todas" else uf,
        origem=origem,
        funcao=None if funcao == "Todas" else funcao,
    )
    st.metric("Registros retornados pela FastAPI", len(filtrados))
    st.dataframe(filtrados, use_container_width=True, hide_index=True)
except (APIIndisponivel, ValueError) as erro:
    st.error(f"Consulta GET falhou: {erro}")

st.subheader("Adicionar dado manual: POST /despesas")
st.info("Registros enviados serão identificados como **manuais/não verificados** e ficam fora da amostra original.")
with st.form("cadastro_despesa", clear_on_submit=True):
    a, b = st.columns(2)
    sigla = a.selectbox("UF do cadastro", list(ESTADOS))
    ano = b.number_input("Ano", min_value=2000, max_value=2100, value=2025, step=1)
    funcao_nova = st.selectbox("Função do cadastro", FUNCOES)
    c, d = st.columns(2)
    valor = c.number_input("Valor da despesa (R$)", min_value=0.0, value=1000.0, step=100.0)
    populacao = d.number_input("População", min_value=1, max_value=300_000_000, value=1_000_000, step=1)
    enviar = st.form_submit_button("Enviar POST para a FastAPI")
if enviar:
    try:
        novo = cadastrar_despesa({
            "sigla": sigla, "ano": int(ano), "funcao": funcao_nova,
            "valor_despesa": float(valor), "populacao": int(populacao),
        })
        st.success(f"Registro criado via POST: {novo['id_registro']} (origem: {novo['origem']}).")
        st.json(novo)
        st.caption("Atualize a página ou selecione 'manual' acima para visualizar o novo cadastro por GET.")
    except APIIndisponivel as erro:
        st.error(f"Cadastro POST falhou: {erro}")

with st.expander("Estatísticas: GET /estatisticas"):
    try:
        st.json(consultar_estatisticas(origem=origem))
    except APIIndisponivel as erro:
        st.error(str(erro))
