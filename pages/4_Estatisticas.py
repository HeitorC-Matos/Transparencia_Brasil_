"""Painel estatístico comparativo: somente dados ilustrativos da amostra original."""
import pandas as pd
import streamlit as st

from utils.analises import formatar_reais
from utils.api_client import APIIndisponivel, consultar_despesas, consultar_estatisticas
from utils.estatisticas_amostra import (
    classificar_estados, comparar_estados, composicao_funcoes,
    estatisticas_por_funcao, matriz_funcoes, per_capita_funcoes,
    resumo_estados, validar_amostra,
)
from utils.ui import aviso_amostra, obter_amostra


def _pct(numero: float | None) -> str:
    return "Não calculável" if numero is None or pd.isna(numero) else f"{numero:+.2f}%".replace(".", ",")


def _moeda(numero: float) -> str:
    return formatar_reais(float(numero))


st.set_page_config(page_title="Estatísticas", page_icon="📈", layout="wide")
st.title("📈 Estatísticas comparativas")
st.caption("São Paulo, Goiás e Bahia · somente os registros ilustrativos, sem incluir os dados oficiais do Siconfi.")
aviso_amostra()

try:
    df = consultar_despesas(origem="amostra_academica")
    resumo_api = consultar_estatisticas(origem="amostra_academica")
    st.caption("Fonte dos registros: consulta HTTP às rotas GET /despesas e GET /estatisticas.")
except (APIIndisponivel, OSError, ValueError) as erro:
    st.warning(f"FastAPI indisponível ({erro}). Exibindo a amostra local, sem integração HTTP ativa.")
    try:
        df = obter_amostra()
    except (OSError, ValueError) as erro_local:
        st.error(f"Não foi possível carregar a amostra: {erro_local}")
        st.stop()
    resumo_api = None

if df.empty:
    st.info("Não há registros da amostra para analisar.")
    st.stop()

try:
    df = validar_amostra(df)
except (ValueError, TypeError) as erro:
    st.error(f"A amostra contém dados inconsistentes: {erro}")
    st.stop()

anos = sorted(int(ano) for ano in df["ano"].unique())
ano = st.selectbox("Ano de referência", anos, index=len(anos) - 1)
base = df.loc[df["ano"].eq(ano)].copy()
estados = sorted(base["estado"].unique().tolist())
funcoes = sorted(base["funcao"].unique().tolist())
totais = resumo_estados(base)
composicao = composicao_funcoes(base)
per_capita = per_capita_funcoes(base)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Soma das funções da amostra", _moeda(base["valor_despesa"].sum()))
col2.metric("Estados", len(estados))
col3.metric("Funções representadas", len(funcoes))
col4.metric("Registros", len(base))
st.caption("A soma exibida reúne apenas as funções da amostra; não corresponde ao orçamento total dos estados.")

if resumo_api is not None:
    with st.expander("Resumo geral retornado pela FastAPI"):
        st.json(resumo_api)

aba_dist, aba_hab, aba_comparar, aba_perfil, aba_matriz = st.tabs([
    "Distribuição das despesas", "Por habitante e rankings",
    "Comparar dois estados", "Perfil de um estado", "Matriz e estatísticas",
])

with aba_dist:
    st.subheader("Composição percentual das três funções")
    st.caption(
        "Cada percentual considera somente a soma de Educação, Saúde e Segurança Pública "
        "presentes na amostra daquele estado, e não todas as despesas do governo."
    )
    estado_dist = st.selectbox("Estado para detalhar a composição", estados, key="estado_dist")
    detalhe = composicao.loc[composicao["estado"].eq(estado_dist)].copy()
    if detalhe["participacao_pct"].isna().any():
        st.warning("Não é possível calcular percentuais quando a soma das despesas é zero.")
    else:
        st.bar_chart(detalhe.set_index("funcao")[["participacao_pct"]])
    tabela_det = detalhe[["funcao", "valor_despesa", "participacao_pct"]].copy()
    tabela_det["valor_despesa"] = tabela_det["valor_despesa"].map(_moeda)
    tabela_det["participacao_pct"] = tabela_det["participacao_pct"].map(
        lambda v: "N/D" if pd.isna(v) else f"{v:.2f}%".replace(".", ",")
    )
    st.dataframe(tabela_det.rename(columns={"funcao": "Função", "valor_despesa": "Valor da amostra", "participacao_pct": "Participação"}),
                 hide_index=True, use_container_width=True)
    st.subheader("Participações entre os estados")
    percentual_matriz = composicao.pivot(index="estado", columns="funcao", values="participacao_pct")
    st.bar_chart(percentual_matriz)
    st.caption("As funções ausentes não são substituídas por valores zero.")

with aba_hab:
    st.subheader("Despesa por habitante e função")
    st.caption("A população de cada estado é utilizada uma vez para cada função, sem somar populações repetidas.")
    tabela_hab = matriz_funcoes(base, "valor_por_habitante")
    st.bar_chart(tabela_hab)
    st.dataframe(tabela_hab.style.format(lambda v: "—" if pd.isna(v) else _moeda(v)), use_container_width=True)

    st.subheader("Ranking comparativo")
    escolha_funcao = st.selectbox("Função considerada no ranking", ["Todas as funções da amostra", *funcoes])
    tipo_ranking = st.radio("Ordenar por", ["Valor absoluto", "Valor por habitante"], horizontal=True)
    criterio = "total" if tipo_ranking == "Valor absoluto" else "valor_por_habitante"
    ranking = classificar_estados(
        base, funcao=None if escolha_funcao == "Todas as funções da amostra" else escolha_funcao,
        criterio=criterio,
    )
    if ranking.empty:
        st.info("Não há valores para a seleção.")
    else:
        visivel = ranking[["posicao", "estado", criterio]].copy()
        visivel[criterio] = visivel[criterio].map(_moeda)
        st.dataframe(visivel.rename(columns={"posicao": "Posição", "estado": "Estado", criterio: tipo_ranking}),
                     hide_index=True, use_container_width=True)
    st.caption("A classificação ordena valores ilustrativos, não qualidade, eficiência ou desempenho dos governos.")

with aba_comparar:
    st.subheader("Comparação direta entre estados")
    if len(estados) < 2:
        st.info("São necessários dois estados para realizar a comparação.")
    else:
        c1, c2 = st.columns(2)
        estado_a = c1.selectbox("Estado de referência (A)", estados, index=0)
        estado_b = c2.selectbox("Estado comparado (B)", estados, index=1)
        funcao_comp = st.selectbox("Área da comparação", ["Todas as funções da amostra", *funcoes])
        if estado_a == estado_b:
            st.warning("Selecione estados diferentes.")
        else:
            try:
                comparacao = comparar_estados(
                    base, estado_a, estado_b,
                    funcao=None if funcao_comp == "Todas as funções da amostra" else funcao_comp,
                )
            except ValueError as erro:
                st.warning(str(erro))
            else:
                absoluto = comparacao["valor_absoluto"]
                hab = comparacao["por_habitante"]
                st.caption(f"Diferenças calculadas como {estado_b} menos {estado_a}; o percentual usa {estado_a} como referência.")
                c1, c2, c3 = st.columns(3)
                c1.metric(f"{estado_a} — valor", _moeda(absoluto["a"]))
                c2.metric(f"{estado_b} — valor", _moeda(absoluto["b"]))
                c3.metric("Diferença absoluta (B − A)", _moeda(absoluto["diferenca"]),
                          delta=_pct(absoluto["diferenca_pct"]))
                st.subheader("Mesma comparação por habitante")
                c1, c2, c3 = st.columns(3)
                c1.metric(f"{estado_a} — por habitante", _moeda(hab["a"]))
                c2.metric(f"{estado_b} — por habitante", _moeda(hab["b"]))
                c3.metric("Diferença por habitante (B − A)", _moeda(hab["diferenca"]),
                          delta=_pct(hab["diferenca_pct"]))
                if absoluto["diferenca_pct"] is None:
                    st.info("A diferença percentual não pode ser calculada quando o valor de referência é zero.")

with aba_perfil:
    st.subheader("Perfil individual")
    estado_perfil = st.selectbox("Estado", estados, key="perfil_estado")
    perfil = totais.loc[totais["estado"].eq(estado_perfil)]
    if perfil.empty:
        st.info("Nenhum registro para este estado.")
    else:
        row = perfil.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Soma das funções", _moeda(row["total"]))
        c2.metric("Por habitante (três funções)", _moeda(row["valor_por_habitante"]))
        c3.metric("População da amostra", f"{int(row['populacao']):,}".replace(",", "."))
        detalhe = per_capita.loc[per_capita["estado"].eq(estado_perfil)]
        st.bar_chart(detalhe.set_index("funcao")[["valor_despesa"]])
        detalhe_visivel = detalhe[["funcao", "valor_despesa", "valor_por_habitante"]].copy()
        for coluna in ("valor_despesa", "valor_por_habitante"):
            detalhe_visivel[coluna] = detalhe_visivel[coluna].map(_moeda)
        st.dataframe(detalhe_visivel.rename(columns={
            "funcao": "Função", "valor_despesa": "Despesa ilustrativa",
            "valor_por_habitante": "Por habitante",
        }), hide_index=True, use_container_width=True)
        if not detalhe.empty:
            maior = detalhe.sort_values("valor_despesa", ascending=False).iloc[0]
            st.caption(f"Maior valor entre as funções da amostra: {maior['funcao']} ({_moeda(maior['valor_despesa'])}).")

with aba_matriz:
    st.subheader("Matriz comparativa — valores absolutos")
    matriz = matriz_funcoes(base)
    st.dataframe(matriz.style.format(lambda v: "—" if pd.isna(v) else _moeda(v)), use_container_width=True)
    st.subheader("Matriz comparativa — por habitante")
    st.dataframe(matriz_funcoes(base, "valor_por_habitante").style.format(lambda v: "—" if pd.isna(v) else _moeda(v)), use_container_width=True)
    st.subheader("Estatísticas descritivas por função")
    descr = estatisticas_por_funcao(base)
    for coluna in ("media", "mediana", "minimo", "maximo", "amplitude"):
        descr[coluna] = descr[coluna].map(_moeda)
    st.dataframe(descr.rename(columns={
        "funcao": "Função", "estados": "Estados na amostra", "media": "Média",
        "mediana": "Mediana", "minimo": "Mínimo", "maximo": "Máximo", "amplitude": "Amplitude",
    }), hide_index=True, use_container_width=True)
    st.caption(
        "Média, mediana, mínimo, máximo e amplitude descrevem somente os valores ilustrativos "
        "disponíveis em cada função. Não são estimativas estatísticas da realidade fiscal."
    )
