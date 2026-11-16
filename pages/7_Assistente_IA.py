"""Interface para processamento de texto usando FastAPI e Qwen local."""
import streamlit as st

from utils.api_client import (
    APIIndisponivel, consultar_status_ia, processar_texto_ia,
)

st.set_page_config(page_title="Assistente IA local", page_icon="🧠", layout="wide")
st.title("Assistente de IA — processamento local")
st.caption("Qwen3-4B-Instruct-2507 | FastAPI | Sem serviço externo de inferência")
st.info(
    "O assistente pode resumir e explicar textos. As despesas apresentadas neste projeto "
    "são uma amostra ilustrativa, e não números oficiais auditados."
)

try:
    estado = consultar_status_ia()
    st.write("**Situação do modelo:**", estado["status"].replace("_", " "))
    if estado["status"] == "arquivos_ausentes":
        st.warning("Os pesos locais ainda não foram baixados. Consulte o guia de instalação local no diretório de documentação.")
    elif estado["status"] == "erro_carregamento":
        st.warning("Houve erro no carregamento local. Verifique CUDA e os logs da API.")
except APIIndisponivel as erro:
    st.error(f"Não foi possível consultar a API FastAPI: {erro}")

with st.form("formulario_llm"):
    texto = st.text_area("Texto para processar", height=200,
                         placeholder="Cole aqui o texto que deseja resumir ou explicar...")
    operacao_exibida = st.radio("Operação", ["Resumo", "Explicação"], horizontal=True)
    limite = st.slider("Limite de tokens gerados", min_value=64, max_value=512,
                       value=256, step=64)
    enviar = st.form_submit_button("Processar pelo Qwen local", type="primary")

if enviar:
    if not texto.strip():
        st.warning("Informe um texto antes de processar.")
    else:
        operacao = "resumo" if operacao_exibida == "Resumo" else "explicacao"
        try:
            with st.spinner("O modelo está processando o texto na GPU local..."):
                resultado = processar_texto_ia(texto, operacao=operacao,
                                               max_novos_tokens=limite)
            st.session_state["assistente_ultimo_resultado"] = resultado
        except APIIndisponivel as erro:
            # Não repetir uma resposta anterior após uma tentativa com erro.
            st.session_state.pop("assistente_ultimo_resultado", None)
            if erro.status_code == 429:
                st.warning(str(erro))
            elif erro.status_code == 422:
                st.warning(str(erro))
            else:
                st.error(str(erro))
            if erro.requisicao_id:
                st.caption(f"Identificador para diagnóstico: {erro.requisicao_id}")

if st.session_state.get("assistente_ultimo_resultado"):
    resposta = st.session_state["assistente_ultimo_resultado"]
    st.subheader("Resultado")
    st.write(resposta["resultado"])
    st.caption(
        f"Modelo: {resposta['modelo']} • Entrada: {resposta['tokens_entrada']} tokens • "
        f"Saída: {resposta['tokens_saida']} tokens • "
        f"Tempo no backend: {resposta['tempo_processamento_ms']} ms"
    )
    st.warning(resposta["aviso"])
