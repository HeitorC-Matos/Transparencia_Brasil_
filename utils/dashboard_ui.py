"""Painel final integrado: visualização, procedência, IA e documentos coletados.

Os valores exibidos vêm exclusivamente da FastAPI. O Qwen nunca calcula totais.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.siconfi import UF_IBGE
from utils.analises import formatar_reais
from utils.api_client import (
    APIIndisponivel, consultar_dados_oficiais, consultar_status_dados_oficiais,
    consultar_status_ia, perguntar_dados_ia, sintetizar_dados_fiscais_ia,
)
from utils.dashboard_final import chave_recorte, montar_visao
from utils.estatisticas_oficiais import FUNCOES, validar_oficiais
from utils.estatisticas_ui import exibir_analises_detalhadas


def _moeda(valor: float | None) -> str:
    return formatar_reais(float(valor)) if valor is not None else "—"


@st.cache_data(ttl=60, show_spinner=False)
def _dados_do_dashboard():
    """Fonte única de entrada: endpoints de dados oficiais, nunca amostra ilustrativa."""
    status = consultar_status_dados_oficiais()
    return status, validar_oficiais(consultar_dados_oficiais())


def _mostrar_erro(erro: APIIndisponivel) -> None:
    if erro.status_code in (422, 429):
        st.warning(str(erro))
    else:
        st.error(str(erro))
    if erro.requisicao_id:
        st.caption("ID de diagnóstico: " + erro.requisicao_id)


def _resultado_qwen(resposta: dict, *, titulo: str):
    st.subheader(titulo)
    st.write(resposta["resultado"])
    st.caption(
        f"Qwen local | {resposta['tokens_entrada']} tokens de entrada | "
        f"{resposta['tokens_saida']} tokens de saída | "
        f"{resposta['tempo_processamento_ms']} ms no backend"
    )
    st.warning(resposta["aviso"])
    with st.expander("Fontes e dados enviados ao modelo"):
        if resposta.get("contexto_calculado"):
            st.text(resposta["contexto_calculado"])
        for fonte in resposta.get("fontes", []):
            st.write(fonte)


def exibir_dashboard():
    """Renderiza a visão nacional com ações de IA explícitas e não automáticas."""
    st.write(
        "Explore e compare despesas públicas das 27 unidades da Federação. "
        "Os gráficos utilizam dados oficiais declarados ao Siconfi; "
        "os insights do Qwen são gerados somente quando solicitados."
    )
    st.info(
        "RREO, Anexo 02, 6º bimestre: despesas **liquidadas** acumuladas de Educação, "
        "Saúde e Segurança Pública. Valores nominais, sem intraorçamentárias e sem "
        "despesas municipais. Não correspondem ao orçamento total nem medem eficiência."
    )
    try:
        status, base = _dados_do_dashboard()
    except (APIIndisponivel, OSError, ValueError, KeyError, TypeError) as erro:
        st.error(f"Painel de gastos indisponível: {erro}")
        st.info("Inicie a FastAPI e confira a base do Siconfi. Nenhuma amostra ilustrativa será usada como substituta.")
        return
    if base.empty:
        st.warning("Nenhum registro oficial disponível para o painel.")
        return
    anos = sorted(base["ano"].unique().tolist())
    ufs_disponiveis = sorted(base["uf"].unique().tolist())
    col1, col2, col3 = st.columns(3)
    col1.metric("UFs disponíveis", base["uf"].nunique())
    col2.metric("Exercícios disponíveis", base["ano"].nunique())
    col3.metric("Registros oficiais", len(base))
    if status.get("situacao") != "completo":
        st.warning("A coleta possui pendências. Valores ausentes não serão substituídos por zero.")

    st.subheader("Escolha os dados para analisar")
    col_uf, col_ano, col_fn = st.columns([2.5, 1, 1.6])
    with col_uf:
        ufs = st.multiselect(
            "Unidades da Federação", ufs_disponiveis, default=ufs_disponiveis,
            format_func=lambda x: f"{x} — {UF_IBGE[x][1]}", key="dashboard_ufs",
        )
    with col_ano:
        ano = st.selectbox("Exercício", anos, index=len(anos) - 1, key="dashboard_ano")
    with col_fn:
        funcoes = st.multiselect(
            "Funções", list(FUNCOES), default=list(FUNCOES), key="dashboard_funcoes",
        )
    if not ufs or not funcoes:
        st.info("Selecione pelo menos uma UF e uma função para prosseguir.")
        return
    visao = montar_visao(base, ano=int(ano), ufs=ufs, funcoes=funcoes, ufs_historico=[])
    chave = chave_recorte(int(ano), ufs, funcoes)
    c1, c2, c3 = st.columns(3)
    c1.metric("UFs com recorte completo", len(visao.ufs_completas))
    c2.metric("Registros no recorte", f"{visao.cobertura}/{visao.combinacoes_esperadas}")
    c3.metric("Subtotal selecionado (R$)", _moeda(visao.soma))
    st.caption(
        "O subtotal considera somente UFs com todas as funções selecionadas disponíveis. "
        "Não equivale ao total de despesas públicas dessas UFs."
    )
    if visao.pendencias:
        st.warning("Existem combinações ausentes; as UFs incompletas foram excluídas das agregações.")
        with st.expander("Consultar dados ausentes"):
            st.dataframe(pd.DataFrame(visao.pendencias), hide_index=True, use_container_width=True)

    aba_graficos, aba_detalhes, aba_ia, aba_fontes = st.tabs([
        "Painel e gráficos", "Análises detalhadas", "Insights com Qwen", "Fontes e critérios",
    ])
    with aba_graficos:
        gra1, gra2 = st.columns(2)
        with gra1:
            st.subheader("Despesas por função")
            if visao.totais_funcao.empty:
                st.info("Não há UFs com recorte completo para calcular os subtotais.")
            else:
                st.bar_chart(visao.totais_funcao.set_index("funcao")[["valor_reais"]])
        with gra2:
            st.subheader("Ranking das UFs")
            if visao.ranking.empty:
                st.info("Não há UFs com dados completos no exercício escolhido.")
            else:
                st.bar_chart(visao.ranking.head(10).set_index("uf")[["valor_reais"]])
                st.caption("Dez maiores subtotais nominais do recorte. Valores absolutos não equivalem a desempenho.")
        st.subheader("Evolução histórica — 2021 a 2025")
        sugestoes = [uf for uf in ("SP", "GO", "BA") if uf in ufs]
        if not sugestoes:
            sugestoes = ufs[:min(3, len(ufs))]
        ufs_hist = st.multiselect(
            "UFs para acompanhar a evolução", ufs, default=sugestoes,
            format_func=lambda x: f"{x} — {UF_IBGE[x][1]}", key="dashboard_historico_ufs",
        )
        if ufs_hist:
            serie = montar_visao(
                base, ano=int(ano), ufs=ufs, funcoes=funcoes, ufs_historico=ufs_hist
            ).serie_historica
            if serie.empty:
                st.info("Não existem séries históricas completas no recorte.")
            else:
                tabela_serie = serie.pivot(index="ano", columns="uf", values="valor_reais").reindex(anos)
                st.line_chart(tabela_serie)
                st.caption("Série nominal; variações não descontam inflação. Ausências permanecem sem valor.")
        else:
            st.info("Escolha ao menos uma UF para visualizar sua evolução.")
        st.divider()
        if st.button("Explicar os gráficos selecionados com Qwen", key="dashboard_explicar_graficos"):
            st.session_state.pop("dashboard_resumo_fiscal", None)
            try:
                with st.spinner("Gerando análise em linguagem natural para os gráficos..."):
                    resp_grafico = sintetizar_dados_fiscais_ia(
                        ufs, int(ano), funcoes, modo="executivo",
                        versao_prompt="estruturado", max_novos_tokens=384,
                    )
                st.session_state["dashboard_resumo_fiscal"] = (chave, resp_grafico)
            except APIIndisponivel as erro:
                _mostrar_erro(erro)
        resposta_grafico = st.session_state.get("dashboard_resumo_fiscal")
        if resposta_grafico and resposta_grafico[0] == chave:
            _resultado_qwen(resposta_grafico[1], titulo="Insights sobre os gráficos")
        with st.expander("Conferir e exportar registros do gráfico"):
            st.dataframe(
                visao.recorte[["uf", "estado", "ano", "funcao", "valor_reais", "fonte_url"]],
                hide_index=True, use_container_width=True,
            )
            st.download_button(
                "Baixar recorte oficial (CSV)",
                data=visao.recorte.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"dashboard_siconfi_{ano}.csv", mime="text/csv",
            )

    with aba_detalhes:
        st.subheader("Comparações e estatísticas detalhadas")
        st.caption("Os seis painéis abaixo utilizam as mesmas UFs, exercício e funções do dashboard.")
        exibir_analises_detalhadas(base, int(ano), ufs, funcoes)

    with aba_ia:
        st.write(
            "**Explicação dos gráficos.** O Python prepara o recorte e seus valores; "
            "o Qwen redige a síntese. A resposta não modifica os indicadores apresentados."
        )
        with st.form("dashboard_sintese_ia"):
            modo = st.selectbox("Formato da explicação", ["executivo", "topicos", "simplificado"],
                                format_func=lambda x: {"executivo": "Resumo executivo", "topicos": "Pontos principais", "simplificado": "Linguagem simples"}[x])
            versao = st.selectbox("Versão do prompt", ["basico", "estruturado", "fundamentado"],
                                  index=1, format_func=lambda x: x.capitalize())
            gerar = st.form_submit_button("Explicar indicadores com Qwen")
        if gerar:
            st.session_state.pop("dashboard_resumo_fiscal", None)
            try:
                with st.spinner("Gerando a explicação local a partir dos indicadores selecionados..."):
                    resp = sintetizar_dados_fiscais_ia(
                        ufs, int(ano), funcoes, modo=modo,
                        versao_prompt=versao, max_novos_tokens=384,
                    )
                st.session_state["dashboard_resumo_fiscal"] = (chave, resp)
            except APIIndisponivel as erro:
                _mostrar_erro(erro)
        salvo = st.session_state.get("dashboard_resumo_fiscal")
        if salvo and salvo[0] == chave:
            _resultado_qwen(salvo[1], titulo="Explicação do recorte")
        elif salvo:
            st.caption("Os filtros mudaram desde a geração. Gere uma nova explicação para o recorte atual.")

        st.divider()
        st.subheader("Perguntar aos dados")
        st.caption("Consultas sobre ranking, comparação, evolução e participação nas três funções. Não há série oficial por habitante integrada.")
        with st.form("dashboard_pergunta"):
            pergunta = st.text_input(
                "Pergunta em linguagem natural",
                placeholder="Qual UF teve maior despesa liquidada com Educação em 2025?",
            )
            complementar = st.checkbox("Complementar resposta com Qwen local", value=True)
            consultar = st.form_submit_button("Consultar o Siconfi")
        if consultar:
            st.session_state.pop("dashboard_pergunta_resposta", None)
            if not pergunta.strip():
                st.warning("Digite uma pergunta antes de consultar.")
            else:
                try:
                    with st.spinner("Consultando os registros oficiais..."):
                        resposta = perguntar_dados_ia(
                            pergunta, ano_referencia=int(ano), usar_qwen=complementar,
                            max_novos_tokens=384,
                        )
                    st.session_state["dashboard_pergunta_resposta"] = (int(ano), resposta)
                except APIIndisponivel as erro:
                    _mostrar_erro(erro)
        pergunta_salva = st.session_state.get("dashboard_pergunta_resposta")
        if pergunta_salva and pergunta_salva[0] != int(ano):
            st.caption("O exercício foi alterado. Refaça a pergunta para consultar o novo contexto.")
        resposta_pergunta = pergunta_salva[1] if pergunta_salva and pergunta_salva[0] == int(ano) else None
        if resposta_pergunta:
            st.success(resposta_pergunta["resposta_calculada"])
            if resposta_pergunta.get("dados"):
                st.dataframe(resposta_pergunta["dados"], hide_index=True, use_container_width=True)
            if resposta_pergunta.get("qwen_executado") and resposta_pergunta.get("explicacao_ia"):
                st.write("**Explicação do Qwen:**", resposta_pergunta["explicacao_ia"])
            if resposta_pergunta.get("aviso_ia"):
                st.warning(resposta_pergunta["aviso_ia"])
            with st.expander("Critério e fontes da resposta"):
                st.write(resposta_pergunta["criterio"])
                for fonte in resposta_pergunta["fontes"]:
                    st.write(fonte)

    with aba_fontes:
        st.subheader("O ciclo de Ciência de Dados no projeto")
        etapas = [
            ("1. Coleta", "API Siconfi (despesas) e extração institucional por Requests/Beautiful Soup e Selenium."),
            ("2. Tratamento", "Validação de UF, exercício, função, duplicidades e critérios do RREO; organização dos textos e metadados."),
            ("3. Análise", "Cálculo em Python de subtotais das três funções, rankings e séries temporais nominais."),
            ("4. Inteligência artificial", "Qwen local resume documentos e explica resultados que o Python já calculou."),
            ("5. Apresentação", "Filtros, gráficos, evidências, perguntas em linguagem natural e exportação dos dados."),
        ]
        for titulo, descricao in etapas:
            st.markdown(f"**{titulo}** — {descricao}")
        st.caption(
            "A sumarização de documentos coletados permanece na seção Assistente IA; "
            "a consulta completa aos registros e métodos de extração está em Dados oficiais."
        )
        st.subheader("Cobertura e procedência")
        st.write(
            f"Situação da coleta: **{status.get('situacao', 'não informada')}** | "
            f"Registros disponíveis: **{len(base)}** | "
            f"Combinações no recorte: **{visao.cobertura}/{visao.combinacoes_esperadas}**."
        )
        st.caption(
            "Somente Educação, Saúde e Segurança Pública. Não há população do IBGE "
            "integrada para per capita, correção pelo IPCA ou indicador de eficiência. "
            "Os dados não comprovam impactos ambientais nem qualidade dos serviços públicos."
        )
        with st.expander("URLs originais do recorte"):
            for url in visao.fontes:
                st.write(url)
        st.write("**Documentação e evidências do projeto:**")
        st.markdown(
            "Consulte `documentacao/DADOS_OFICIAIS_SICONFI.md`, "
            "`documentacao/SUMARIZACAO_COM_LLM.md` e "
            "`documentacao/AVALIACAO_EXPERIMENTAL_PROMPTS.md`."
        )
        try:
            status_ia = consultar_status_ia()
            st.caption("Estado do Qwen local: " + str(status_ia.get("status", "não informado")))
        except APIIndisponivel:
            st.caption("Estado do Qwen não disponível no momento; gráficos e dados continuam acessíveis.")
