"""Interface de perguntas fiscais, documentos, síntese e texto livre."""
from __future__ import annotations

from decimal import Decimal

import streamlit as st

from utils.api_client import (
    APIIndisponivel, consultar_status_ia, listar_documentos_ia,
    processar_texto_ia, resumir_documento_ia, sintetizar_dados_fiscais_ia,
    perguntar_dados_ia,
)

st.set_page_config(page_title="Assistente IA local", page_icon="🧠", layout="wide")
st.title("Assistente IA — Transparência Brasil")
st.caption("Qwen3-4B-Instruct-2507 | Inferência local por FastAPI | Resumos fundamentados")
st.info(
    "A amostra ilustrativa e os dados oficiais do Siconfi são bases distintas. "
    "Os valores oficiais são declarações dos entes e não foram auditados pela aplicação. "
    "Confirme as informações produzidas por IA nas fontes originais."
)

try:
    estado = consultar_status_ia()
    st.write("**Situação do modelo:**", estado["status"].replace("_", " "))
    if estado["status"] == "arquivos_ausentes":
        st.warning("Pesos locais não encontrados. Verifique a pasta do Qwen.")
    elif estado["status"] == "erro_carregamento":
        st.warning("Houve erro ao carregar o modelo. Confira CUDA e os logs da API.")
except APIIndisponivel as erro:
    st.error(f"Não foi possível consultar a FastAPI: {erro}")


MODOS = {"Resumo executivo": "executivo", "Pontos principais": "topicos",
         "Linguagem simples": "simplificado"}
VERSOES = {"Fundamentado (recomendado)": "fundamentado",
           "Estruturado": "estruturado", "Básico": "basico"}


def apresentar_resposta(chave: str):
    resposta = st.session_state.get(chave)
    if not resposta:
        return
    st.subheader("Resultado")
    st.write(resposta["resultado"])
    if resposta.get("contexto_calculado"):
        with st.expander("Valores calculados pelo Python e enviados ao modelo"):
            st.text(resposta["contexto_calculado"])
    if resposta.get("fontes"):
        with st.expander("Fontes utilizadas", expanded=True):
            for origem in resposta["fontes"]:
                st.write(origem)
    st.caption(
        f"Modelo: {resposta['modelo']} | Entrada: {resposta['tokens_entrada']} tokens | "
        f"Saída: {resposta['tokens_saida']} tokens | "
        f"Tempo no backend: {resposta['tempo_processamento_ms']} ms"
    )
    if resposta.get("etapas_geracao"):
        st.caption(f"Etapas de geração: {resposta['etapas_geracao']} | "
                   f"Prompt: {resposta['versao_prompt']}")
    st.warning(resposta["aviso"])


def tratar_erro(erro: APIIndisponivel):
    if erro.status_code in (422, 429):
        st.warning(str(erro))
    else:
        st.error(str(erro))
    if erro.requisicao_id:
        st.caption(f"Identificador para diagnóstico: {erro.requisicao_id}")


def exibir_consulta(chave: str) -> None:
    resposta_fiscal = st.session_state.get(chave)
    if not resposta_fiscal:
        return
    institucional = resposta_fiscal.get("tipo") == "ods16"
    st.subheader("Relação com o ODS 16 e Governança" if institucional else
                 "Resposta calculada com os dados oficiais")
    st.success(resposta_fiscal["resposta_calculada"])
    for nota in resposta_fiscal.get("observacoes", []):
        st.caption(nota)
    if not institucional:
        st.write("**Registros utilizados**")
        linhas_exibidas = []
        for registro in resposta_fiscal["dados"]:
            linha = {
                "UF": registro["uf"],
                "Estado": registro["estado"],
                "Ano": registro["ano"],
                "Função": registro["funcao"],
                "Despesa liquidada": "R$ " + f"{Decimal(str(registro['valor_reais'])):,.2f}".replace(",", "#").replace(".", ",").replace("#", "."),
            }
            if registro.get("posicao") is not None:
                linha = {"Posição": registro["posicao"], **linha}
            if registro.get("variacao_nominal_percentual") is not None:
                linha["Variação nominal"] = f"{Decimal(str(registro['variacao_nominal_percentual'])):.2f}%".replace(".", ",")
            if registro.get("participacao_percentual") is not None:
                linha["Participação no subtotal"] = f"{Decimal(str(registro['participacao_percentual'])):.2f}%".replace(".", ",")
            linhas_exibidas.append(linha)
        st.dataframe(linhas_exibidas, use_container_width=True, hide_index=True)

    if resposta_fiscal.get("qwen_executado"):
        st.subheader("Explicação do Qwen local" if institucional else
                     "Explicação complementar do Qwen")
        st.write(resposta_fiscal["explicacao_ia"])
        st.caption(
            f"Modelo: {resposta_fiscal.get('modelo')} | "
            f"Tempo de inferência: {resposta_fiscal.get('tempo_processamento_ms')} ms"
        )
    if resposta_fiscal.get("aviso_ia"):
        st.warning(resposta_fiscal["aviso_ia"])
    with st.expander("Critério metodológico e fontes", expanded=True):
        st.write(resposta_fiscal["criterio"])
        if not institucional:
            st.caption("Fontes oficiais declaradas, sem auditoria independente.")
        for url in resposta_fiscal["fontes"]:
            st.write(url)


aba_perguntas, aba_ods, aba_documentos, aba_fiscal, aba_livre = st.tabs(
    ["Perguntar aos dados", "ODS 16 e Governança", "Documentos coletados", "Síntese fiscal", "Texto livre"]
)

with aba_perguntas:
    st.write(
        "Faça perguntas sobre **Educação**, **Saúde** e **Segurança Pública** nas "
        "27 UFs (2021–2025). O Python consulta e calcula os valores oficiais; "
        "o Qwen pode complementar a explicação sem substituir a resposta calculada. "
        "Este mesmo campo também reconhece perguntas sobre o Transparência Brasil, o ODS 16 e o ESG."
    )
    st.caption(
        "Exemplos: Qual UF mais gastou com Educação em 2025? | "
        "Quanto Goiás gastou com Saúde em 2024? | "
        "Compare SP e BA na Segurança Pública em 2025. | "
        "Como evoluiu a Educação no DF de 2021 a 2025? | "
        "Qual a participação da Saúde nas três funções em Minas Gerais em 2025? | "
        "Como o Transparência Brasil contribui para o ODS 16?"
    )
    with st.form("consulta_linguagem_natural"):
        ano_referencia = st.selectbox(
            "Ano utilizado quando a pergunta não informa o exercício",
            options=[2025, 2024, 2023, 2022, 2021], key="ano_pergunta",
        )
        pergunta = st.text_area(
            "Pergunta sobre despesas ou sobre o projeto e o ODS 16",
            height=110,
            placeholder="Qual foi a UF com maior despesa com Educação em 2025?",
            key="pergunta_fiscal",
        )
        usar_qwen = st.checkbox(
            "Complementar com explicação do Qwen local",
            value=True, key="usar_qwen_pergunta",
        )
        limite_pergunta = st.slider(
            "Máximo de tokens da explicação", 96, 384, 384, 32,
            key="tokens_pergunta", disabled=not usar_qwen,
        )
        consultar = st.form_submit_button("Responder pergunta", type="primary")
    if consultar:
        st.session_state.pop("resposta_pergunta_oficial", None)
        if not pergunta.strip():
            st.warning("Informe uma pergunta antes de consultar.")
        else:
            try:
                with st.spinner("Consultando os dados e preparando a resposta..."):
                    st.session_state["resposta_pergunta_oficial"] = perguntar_dados_ia(
                        pergunta, ano_referencia=ano_referencia,
                        usar_qwen=usar_qwen, max_novos_tokens=limite_pergunta,
                    )
            except APIIndisponivel as erro:
                tratar_erro(erro)
    exibir_consulta("resposta_pergunta_oficial")


with aba_ods:
    st.write(
        "**ODS 16 e Governança (ESG)** — entenda a ligação entre o Transparência Brasil, "
        "as metas 16.6 e 16.10 da ONU, a transparência fiscal e o acesso à informação. "
        "O Qwen usa informações verificadas do projeto e o documento da ONU coletado pelo próprio sistema."
    )
    st.info(
        "Esta categoria explica o papel do projeto na transparência e no controle social. "
        "Ela não mede o cumprimento do ODS 16, não avalia a eficiência dos governos "
        "e não substitui as consultas numéricas em Perguntar aos dados."
    )
    with st.form("consulta_ods16_governanca"):
        pergunta_padrao = st.selectbox(
            "Escolha um assunto",
            options=[
                "Como o Transparência Brasil está relacionado ao ODS 16?",
                "Como o projeto contribui para a meta 16.6?",
                "Qual a relação com a meta 16.10 e o acesso à informação?",
                "Como o Transparência Brasil se relaciona à Governança do ESG?",
                "Como os gráficos e a IA apoiam o controle social?",
            ],
        )
        pergunta_personalizada = st.text_area(
            "Ou escreva sua própria pergunta (opcional)",
            height=90, placeholder="Como a IA pode facilitar o acesso a informações públicas?",
            key="pergunta_ods16",
        )
        usar_qwen_ods = st.checkbox("Gerar explicação pelo Qwen local", value=True,
                                    key="usar_qwen_ods16")
        limite_ods = st.slider("Máximo de tokens", 96, 384, 384, 32,
                              key="tokens_ods16", disabled=not usar_qwen_ods)
        enviar_ods = st.form_submit_button("Explicar ODS 16 e Governança", type="primary")
    if enviar_ods:
        st.session_state.pop("resposta_ods16", None)
        pergunta_ods = (pergunta_personalizada.strip() + " — no contexto do ODS 16"
                        if pergunta_personalizada.strip() else pergunta_padrao)
        try:
            with st.spinner("Consultando a fonte da ONU e explicando a relação com o projeto..."):
                st.session_state["resposta_ods16"] = perguntar_dados_ia(
                    pergunta_ods, usar_qwen=usar_qwen_ods, max_novos_tokens=limite_ods,
                )
        except APIIndisponivel as erro:
            tratar_erro(erro)
    exibir_consulta("resposta_ods16")


with aba_documentos:
    st.write("Selecione um texto já coletado pelo projeto, sem precisar copiar e colar seu conteúdo.")
    try:
        catalogo = listar_documentos_ia()
    except APIIndisponivel as erro:
        catalogo = []
        st.warning(f"Não foi possível obter o catálogo documental: {erro}")
    if not catalogo:
        st.info("Nenhum documento disponível. Confira as coletas e a FastAPI.")
    else:
        rotulos = {doc["id"]: f"{doc['titulo']} — {doc['origem']}" for doc in catalogo}
        with st.form("sumarizacao_documental"):
            doc_id = st.selectbox("Documento", options=list(rotulos),
                                  format_func=lambda id_: rotulos[id_])
            modo_d = st.selectbox("Formato", options=list(MODOS))
            versao_d = st.selectbox("Engenharia de prompts", options=list(VERSOES))
            tokens_d = st.slider("Máximo de tokens", 96, 384, 384, 32, key="tokens_doc")
            gerar_d = st.form_submit_button("Resumir documento com Qwen", type="primary")
        selecionado = next(d for d in catalogo if d["id"] == doc_id)
        st.caption(f"Método: {selecionado['metodo']} | Coleta: {selecionado['data_coleta']} | "
                   f"{selecionado['caracteres']} caracteres")
        st.write("Fonte original:", selecionado["url"])
        if gerar_d:
            st.session_state.pop("resultado_documental", None)
            try:
                with st.spinner("Gerando a síntese dos dados documentais na GPU local..."):
                    st.session_state["resultado_documental"] = resumir_documento_ia(
                        doc_id, modo=MODOS[modo_d], versao_prompt=VERSOES[versao_d],
                        max_novos_tokens=tokens_d,
                    )
            except APIIndisponivel as erro:
                tratar_erro(erro)
        apresentar_resposta("resultado_documental")

with aba_fiscal:
    st.write(
        "A aplicação calcula os valores oficiais selecionados; o modelo apenas redige "
        "uma explicação. A soma das três funções não representa todo o orçamento."
    )
    from services.siconfi import UF_IBGE, FUNCOES_CODIGO
    ufs_ordenadas = sorted(UF_IBGE)
    with st.form("sumarizacao_fiscal"):
        ano_f = st.selectbox("Exercício", options=[2025, 2024, 2023, 2022, 2021])
        ufs_f = st.multiselect("UFs (uma, várias ou todas)", options=ufs_ordenadas,
                              default=["BA", "GO", "SP"],
                              format_func=lambda uf: f"{uf} — {UF_IBGE[uf][1]}")
        funcoes_f = st.multiselect("Funções de governo", options=list(FUNCOES_CODIGO),
                                  default=list(FUNCOES_CODIGO))
        modo_f = st.selectbox("Formato da síntese", options=list(MODOS), key="modo_fiscal")
        versao_f = st.selectbox("Engenharia de prompts", options=list(VERSOES),
                                key="versao_fiscal")
        tokens_f = st.slider("Máximo de tokens", 96, 384, 384, 32, key="tokens_fiscal")
        gerar_f = st.form_submit_button("Explicar indicadores com Qwen", type="primary")
    if gerar_f:
        st.session_state.pop("resultado_fiscal", None)
        if not ufs_f or not funcoes_f:
            st.warning("Selecione pelo menos uma UF e uma função de governo.")
        else:
            try:
                with st.spinner("Calculando os dados e gerando a síntese na GPU local..."):
                    st.session_state["resultado_fiscal"] = sintetizar_dados_fiscais_ia(
                        ufs_f, ano_f, funcoes_f, modo=MODOS[modo_f],
                        versao_prompt=VERSOES[versao_f], max_novos_tokens=tokens_f,
                    )
            except APIIndisponivel as erro:
                tratar_erro(erro)
    apresentar_resposta("resultado_fiscal")

with aba_livre:
    st.write("Use também o processamento livre de texto já disponível na aplicação.")
    with st.form("formulario_llm"):
        texto = st.text_area("Texto para processar", height=200,
                             placeholder="Cole aqui o texto que deseja resumir ou explicar...")
        operacao_exibida = st.radio("Operação", ["Resumo", "Explicação"], horizontal=True)
        limite = st.slider("Limite de tokens gerados", min_value=64, max_value=512,
                           value=384, step=64)
        enviar = st.form_submit_button("Processar pelo Qwen local")
    if enviar:
        st.session_state.pop("assistente_ultimo_resultado", None)
        if not texto.strip():
            st.warning("Informe um texto antes de processar.")
        else:
            try:
                with st.spinner("O modelo está processando o texto na GPU local..."):
                    st.session_state["assistente_ultimo_resultado"] = processar_texto_ia(
                        texto, operacao="resumo" if operacao_exibida == "Resumo" else "explicacao",
                        max_novos_tokens=limite,
                    )
            except APIIndisponivel as erro:
                tratar_erro(erro)
    apresentar_resposta("assistente_ultimo_resultado")
