"""Detalhamento das estatísticas fiscais, reutilizando o recorte selecionado no dashboard.

A origem e os filtros são os mesmos do painel nacional; não há consultas duplicadas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.siconfi import UF_IBGE
from utils.analises import formatar_reais
from utils.estatisticas_oficiais import (
    FUNCOES, agregar_ufs, agregacao_regional, comparar, composicao,
    descricao, historico, selecionar,
)


def moeda(valor: float) -> str:
    return formatar_reais(float(valor))


def percentual(valor: float | None, *, sinal: bool = False) -> str:
    if valor is None or pd.isna(valor):
        return "Não calculável"
    return f"{valor:{'+' if sinal else ''}.2f}%".replace(".", ",")


def nome_uf(sigla: str) -> str:
    return f"{sigla} — {UF_IBGE[sigla][1]}"


def exibir_analises_detalhadas(base: pd.DataFrame, ano: int, ufs: list[str],
                                funcoes_selecionadas: list[str]) -> None:
    """Exibe os seis painéis legados sem recriar filtros globais nem consultar APIs."""
    anos = sorted(int(a) for a in base["ano"].unique())
    recorte = selecionar(base, ano=ano, ufs=ufs, funcoes=funcoes_selecionadas)
    resumo, ausentes = agregar_ufs(base, ano=ano, ufs=ufs, funcoes=funcoes_selecionadas)
    if ausentes:
        st.warning(
            f"{len(ausentes)} UF(s) não têm todas as funções exigidas no recorte "
            "e não entram nos rankings e nas somas."
        )
    aba_dist, aba_rank, aba_comp, aba_perfil, aba_hist, aba_matriz = st.tabs([
        "Distribuição", "Rankings e regiões", "Comparar duas UFs",
        "Perfil de uma UF", "Evolução histórica", "Matriz e estatísticas",
    ])

    with aba_dist:
        st.subheader("Composição das três funções")
        st.caption(
            "Os percentuais mostram a distribuição entre Educação, Saúde e Segurança Pública, "
            "não a participação de cada função no orçamento total."
        )
        uf_dist = st.selectbox("UF para detalhar a composição", ufs, format_func=nome_uf, key="estat_uf_dist")
        compos = composicao(base, ano=ano, uf=uf_dist)
        if compos.empty:
            st.warning("Não existem dados completos das três funções para calcular a composição desta UF/ano.")
        else:
            if compos["participacao_pct"].isna().any():
                st.info("A soma das três funções é zero; não é possível calcular uma participação percentual.")
            else:
                st.bar_chart(compos.set_index("funcao")[["participacao_pct"]])
            tabela = compos[["funcao", "valor_reais", "participacao_pct"]].copy()
            tabela["valor_reais"] = tabela["valor_reais"].map(moeda)
            tabela["participacao_pct"] = tabela["participacao_pct"].map(percentual)
            st.dataframe(tabela.rename(columns={
                "funcao": "Função", "valor_reais": "Despesa liquidada", "participacao_pct": "Participação nas três funções",
            }), hide_index=True, use_container_width=True)
        st.subheader("Comparar a composição entre UFs")
        pct_linhas = []
        for uf in ufs:
            quadro = composicao(base, ano=ano, uf=uf)
            if not quadro.empty:
                pct_linhas.extend(quadro[["uf", "funcao", "participacao_pct"]].to_dict("records"))
        if pct_linhas:
            pct_tabela = pd.DataFrame(pct_linhas).pivot(index="uf", columns="funcao", values="participacao_pct")
            st.bar_chart(pct_tabela)
            st.dataframe(pct_tabela.style.format(lambda v: "—" if pd.isna(v) else percentual(v)), use_container_width=True)
        else:
            st.info("Não há UFs com as três funções completas para esta comparação.")

    with aba_rank:
        st.subheader("Ranking de despesas liquidadas — valores nominais")
        if resumo.empty:
            st.info("Não há UFs com dados completos para formar um ranking.")
        else:
            ranking = resumo.copy()
            ranking.insert(0, "posição", range(1, len(ranking) + 1))
            st.bar_chart(ranking.set_index("uf")[["valor_reais"]], height=560)
            vis = ranking[["posição", "uf", "estado", "valor_reais"]].copy()
            vis["valor_reais"] = vis["valor_reais"].map(moeda)
            st.dataframe(vis.rename(columns={
                "posição": "Posição", "uf": "UF", "estado": "Estado", "valor_reais": "Valor",
            }), hide_index=True, use_container_width=True)
        st.caption("O ranking compara volumes de despesas, não eficiência, qualidade dos serviços ou gestão pública.")
        st.subheader("Comparação entre grandes regiões")
        regioes = agregacao_regional(resumo, ufs)
        validas = regioes.loc[regioes["situacao"].eq("completo")].copy()
        if not validas.empty:
            st.bar_chart(validas.set_index("regiao")[["valor_reais"]])
        else:
            st.info("Não há regiões com todas as UFs selecionadas e dados completos para esta análise.")
        st.caption("Só são calculados totais regionais quando todas as UFs da região estão selecionadas e completas.")
        st.dataframe(regioes[["regiao", "situacao", "ufs_com_dados", "ufs_esperadas", "ufs_ausentes"]].rename(columns={
            "regiao": "Região", "situacao": "Cobertura", "ufs_com_dados": "UFs válidas",
            "ufs_esperadas": "UFs esperadas", "ufs_ausentes": "Não incluídas/ausentes",
        }), hide_index=True, use_container_width=True)

    with aba_comp:
        st.subheader("Comparação direta entre duas UFs")
        if len(ufs) < 2:
            st.info("Selecione pelo menos duas UFs no filtro principal para realizar a comparação.")
        else:
            c_a, c_b = st.columns(2)
            uf_a = c_a.selectbox("UF A — referência", ufs, index=0, format_func=nome_uf, key="comparar_a")
            uf_b = c_b.selectbox("UF B — comparação", ufs, index=1, format_func=nome_uf, key="comparar_b")
            try:
                diferencas = comparar(base, ano=ano, uf_a=uf_a, uf_b=uf_b,
                                     funcoes=funcoes_selecionadas)
            except ValueError as erro:
                st.warning(str(erro))
            else:
                st.caption(f"Diferença calculada como {uf_b} menos {uf_a}; percentual relativo a {uf_a}.")
                x, y, z = st.columns(3)
                x.metric(f"{uf_a} — valor", moeda(diferencas["valor_a"]))
                y.metric(f"{uf_b} — valor", moeda(diferencas["valor_b"]))
                z.metric("Diferença B − A", moeda(diferencas["diferenca_reais"]),
                         delta=percentual(diferencas["diferenca_pct"], sinal=True))
                detalhes = selecionar(base, ano=ano, ufs=[uf_a, uf_b], funcoes=funcoes_selecionadas)
                graf = detalhes.pivot(index="funcao", columns="uf", values="valor_reais")
                st.bar_chart(graf)
                st.caption("Se o valor de referência for zero, a diferença percentual não é calculável.")

    with aba_perfil:
        st.subheader("Perfil estatístico de uma UF")
        uf_perfil = st.selectbox("Escolha uma UF", ufs, format_func=nome_uf, key="estat_perfil")
        st.caption("O perfil apresenta as três funções independentemente do filtro de função principal.")
        perfil = composicao(base, ano=ano, uf=uf_perfil)
        if perfil.empty:
            st.warning("A UF não possui as três funções disponíveis neste exercício.")
        else:
            p1, p2 = st.columns(2)
            p1.metric("Soma das três funções", moeda(perfil["valor_reais"].sum()))
            maior = perfil.loc[perfil["valor_reais"].idxmax()]
            p2.metric("Função com maior despesa", maior["funcao"])
            st.bar_chart(perfil.set_index("funcao")[["valor_reais"]])
            st.dataframe(perfil.assign(valor_reais=perfil["valor_reais"].map(moeda))
                         .rename(columns={"uf": "UF", "funcao": "Função", "valor_reais": "Valor (R$)",
                                          "participacao_pct": "Participação (%)"}),
                         hide_index=True, use_container_width=True)
        st.caption("Ainda não há despesa por habitante oficial: a série populacional do IBGE não foi integrada.")

    with aba_hist:
        st.subheader("Evolução nominal das despesas — 2021 a 2025")
        st.caption("Utiliza os mesmos critérios do filtro de função, mas exibe a série de todos os anos disponíveis.")
        padrao = [uf for uf in ("SP", "GO", "BA") if uf in ufs]
        if not padrao:
            padrao = ufs[:min(len(ufs), 3)]
        ufs_hist = st.multiselect(
            "UFs para evolução histórica", ufs, default=padrao,
            format_func=nome_uf, key="estat_hist",
        )
        if not ufs_hist:
            st.info("Escolha ao menos uma UF para acompanhar a evolução histórica.")
        else:
            serie = historico(base, ufs=ufs_hist, funcoes=funcoes_selecionadas)
            if serie.empty:
                st.info("Não existem séries completas para as UFs selecionadas.")
            else:
                st.line_chart(serie.pivot(index="ano", columns="uf", values="valor_reais")
                              .reindex(sorted(anos)))
                tabela_serie = serie.copy()
                tabela_serie["valor_reais"] = tabela_serie["valor_reais"].map(moeda)
                tabela_serie["variacao_nominal_pct"] = tabela_serie["variacao_nominal_pct"].map(percentual)
                st.dataframe(tabela_serie.rename(columns={
                    "uf": "UF", "estado": "Estado", "ano": "Ano", "valor_reais": "Valor (R$)",
                    "variacao_nominal_pct": "Variação nominal anual",
                }), hide_index=True, use_container_width=True)
                st.caption(
                    "Variações calculadas apenas entre anos consecutivos com base anterior diferente de zero. "
                    "Os valores não estão corrigidos pela inflação."
                )

    with aba_matriz:
        st.subheader("Matriz UF × função")
        if recorte.empty:
            st.info("Sem registros para o recorte escolhido.")
        else:
            tabela = recorte.pivot(index="uf", columns="funcao", values="valor_reais")
            tabela = tabela.reindex(index=ufs, columns=funcoes_selecionadas)
            st.dataframe(tabela.style.format(lambda v: "—" if pd.isna(v) else moeda(v)),
                         use_container_width=True)
        st.subheader("Estatísticas descritivas do recorte")
        info = descricao(resumo)
        if info is None:
            st.info("Não há dados completos suficientes para calcular estatísticas.")
        else:
            d1, d2, d3 = st.columns(3)
            d1.metric("Média", moeda(info["media"]))
            d2.metric("Mediana", moeda(info["mediana"]))
            d3.metric("Amplitude", moeda(info["amplitude"]))
            d4, d5, d6 = st.columns(3)
            d4.metric("Mínimo", moeda(info["minimo"]))
            d5.metric("Máximo", moeda(info["maximo"]))
            d6.metric("UFs utilizadas", info["quantidade_ufs"])
        st.caption("As estatísticas descrevem os valores selecionados. Não constituem inferência, previsão ou avaliação de eficiência.")
        st.subheader("Registros oficiais e fontes")
        st.dataframe(
            recorte[["uf", "estado", "ano", "funcao", "valor_reais", "fonte_url"]],
            hide_index=True, use_container_width=True,
            column_config={"fonte_url": st.column_config.LinkColumn("Consulta de origem")},
        )
        st.download_button(
            "Baixar registros selecionados (CSV)",
            data=recorte.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"estatisticas_siconfi_{ano}.csv", mime="text/csv",
        )

