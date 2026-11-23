"""Painel de consultas ao RREO Anexo 02, com registros validados e rastreáveis."""
from __future__ import annotations

import streamlit as st

from services.siconfi import FUNCOES_CODIGO, UF_IBGE
from utils.api_client import (
    APIIndisponivel, consultar_dados_oficiais, consultar_regioes_oficiais, consultar_serie_oficial,
    consultar_status_dados_oficiais, processar_texto_ia,
)

st.set_page_config(page_title="Dados oficiais — Siconfi", page_icon="🏛️", layout="wide")
st.title("🏛️ Despesas oficiais declaradas ao Siconfi")
st.caption("RREO • Anexo 02 • 6º bimestre • Despesas liquidadas acumuladas • Exercícios de 2021 a 2025")
st.warning(
    "Os valores foram declarados pelos governos ao Siconfi; não representam auditoria "
    "independente. São despesas dos governos estaduais/distrital, sem gastos dos "
    "municípios. A análise utiliza valores nominais e exclui intraorçamentárias."
)

try:
    estado = consultar_status_dados_oficiais()
except APIIndisponivel as erro:
    st.error(f"Não foi possível verificar a base oficial pela FastAPI: {erro}")
    st.stop()

if estado["situacao"] == "nao_coletado":
    st.info(
        "A base fiscal oficial ainda não foi importada. Para fazer a coleta com o Siconfi, "
        "execute `python scripts/coletar_siconfi.py --ufs SP GO BA` no terminal. "
        "Após validar a coleta piloto, use `--todas` para as 27 UFs."
    )
    st.stop()

if estado["situacao"] == "indisponivel":
    st.error("Não há registros oficiais válidos. Consulte o manifesto de pendências.")
    st.stop()

st.write(
    f"**Cobertura validada:** {estado['combinacoes_validas']} de "
    f"{estado['total_combinacoes']} combinações UF/ano • "
    f"{estado['registros_validados']} registros de função."
)
if estado["situacao"] != "completo":
    st.warning("A última coleta é parcial. Não interprete ausência de dados como despesa zero.")
    with st.expander("Pendências da coleta"):
        st.dataframe(estado.get("combinacoes_pendentes", []), use_container_width=True)

try:
    quadro = consultar_dados_oficiais()
except (APIIndisponivel, ValueError) as erro:
    st.error(f"Não foi possível carregar os dados fiscais: {erro}")
    st.stop()

if quadro.empty:
    st.info("Nenhum registro validado disponível.")
    st.stop()

anos = sorted(int(a) for a in quadro["ano"].unique())
ano = st.selectbox("Exercício financeiro", anos, index=len(anos) - 1)
funcao = st.selectbox("Função de governo", list(FUNCOES_CODIGO))
lista_ufs = sorted(quadro["uf"].unique())
ufs = st.multiselect(
    "Unidades da Federação", lista_ufs, default=lista_ufs,
    format_func=lambda x: f"{x} — {UF_IBGE[x][1]}",
)
selecionado = quadro.loc[
    quadro["ano"].eq(ano) & quadro["funcao"].eq(funcao) & quadro["uf"].isin(ufs)
].copy()
if selecionado.empty:
    st.info("Não existem registros validados para essa seleção. Isso não equivale a valor zero.")
    st.stop()

selecionado = selecionado.sort_values("valor_reais", ascending=False)
st.metric("Governos com dados para a seleção", len(selecionado))
st.subheader("Comparação nominal — despesas liquidadas acumuladas")
st.bar_chart(selecionado.set_index("uf")[["valor_reais"]])
st.caption("Valores nominais em reais, não corrigidos pela inflação; diferenças não demonstram eficiência ou qualidade do gasto.")
st.subheader("Registros e fontes")
st.dataframe(
    selecionado[["uf", "estado", "ano", "funcao", "valor_reais", "fonte_url"]],
    use_container_width=True, hide_index=True,
    column_config={"fonte_url": st.column_config.LinkColumn("Consulta original")},
)
st.download_button(
    "Baixar dados filtrados (CSV)",
    data=selecionado.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"siconfi_{ano}_{FUNCOES_CODIGO[funcao]}.csv", mime="text/csv",
)

st.subheader("Comparação por grandes regiões")
try:
    agregados = consultar_regioes_oficiais(ano, funcao)["dados"]
    import pandas as pd
    resumo_regional = pd.DataFrame(agregados)
    if not resumo_regional.empty:
        validos = resumo_regional.loc[resumo_regional["situacao"].eq("completo")].copy()
        if not validos.empty:
            validos["valor_reais"] = pd.to_numeric(validos["valor_reais"])
            st.bar_chart(validos.set_index("regiao")[["valor_reais"]])
        else:
            st.info("Nenhuma região possui cobertura completa neste ano/função.")
        st.dataframe(resumo_regional, use_container_width=True, hide_index=True)
        st.caption("Regiões incompletas não recebem total, evitando interpretar ausência como zero.")
except (APIIndisponivel, ValueError) as erro:
    st.warning(f"Agregação regional indisponível: {erro}")

st.subheader("Evolução anual por unidade")
uf_serie = st.selectbox("UF para série histórica", lista_ufs,
                        format_func=lambda x: f"{x} — {UF_IBGE[x][1]}")
try:
    serie = consultar_serie_oficial(uf_serie, funcao)
    if serie["dados"]:
        import pandas as pd
        df_serie = pd.DataFrame(serie["dados"])
        df_serie["valor_reais"] = pd.to_numeric(df_serie["valor_reais"])
        st.line_chart(df_serie.set_index("ano")[["valor_reais"]])
        st.dataframe(df_serie, use_container_width=True, hide_index=True)
        st.caption("Variação apenas para anos consecutivos; valores nominais, sem deflator.")
    else:
        st.info("Esta unidade não possui dados suficientes para a série selecionada.")
except (APIIndisponivel, ValueError) as erro:
    st.warning(f"Série histórica indisponível: {erro}")

st.subheader("Explicação com IA local")
st.write("A análise utiliza somente os registros numéricos exibidos nesta seleção.")
if st.button("Explicar os resultados com Qwen", type="primary"):
    texto = (
        "DADOS OFICIAIS DECLARATÓRIOS DO SICONFI — NÃO AUDITADOS. "
        f"RREO Anexo 02, 6º bimestre, função {funcao}, exercício {ano}, "
        "despesas liquidadas acumuladas, excluídas intraorçamentárias. "
        "Valores nominais em reais. Abrangência dos governos estaduais/distrital "
        "(não inclui governos municipais). Dados selecionados: "
        + "; ".join(f"{r.uf}: R$ {r.valor_reais:,.2f}" for r in selecionado.itertuples())
        + ". Explique as diferenças, sem especular sobre causalidade, eficiência "
          "ou políticas públicas não documentadas. Cite a fonte Siconfi/RREO Anexo 02."
    )
    try:
        with st.spinner("Qwen processando as informações na GPU local..."):
            resposta = processar_texto_ia(texto, operacao="explicacao", max_novos_tokens=384)
        st.write(resposta["resultado"])
        st.caption(f"Gerado localmente com {resposta['modelo']}. Confira os dados e as fontes da tabela.")
    except APIIndisponivel as erro:
        st.error(f"Não foi possível gerar a explicação: {erro}")
