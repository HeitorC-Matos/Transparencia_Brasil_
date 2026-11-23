"""Indicadores reprodutíveis da base Siconfi: somente três funções do RREO.

Os totais consolidados exigem todas as funções selecionadas para cada UF/ano;
a ausência de uma função não é convertida em despesa zero. O módulo não usa
valores ilustrativos, população presumida nem indicadores de eficiência.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from services.siconfi import FUNCOES_CODIGO, REGIOES, UF_IBGE

FUNCOES = tuple(FUNCOES_CODIGO)
COLUNAS_NECESSARIAS = {
    "uf", "ano", "funcao", "valor_reais", "codigo_funcao", "periodo",
    "cod_conta", "fonte_url", "estado",
}


def validar_oficiais(dados: pd.DataFrame) -> pd.DataFrame:
    """Valida os registros recebidos da FastAPI, sem alterar a entrada."""
    if not isinstance(dados, pd.DataFrame):
        raise ValueError("A base oficial precisa ser uma tabela.")
    faltantes = COLUNAS_NECESSARIAS - set(dados.columns)
    if faltantes:
        raise ValueError("Colunas ausentes: " + ", ".join(sorted(faltantes)))
    base = dados.copy(deep=True)
    if base.empty:
        return base
    try:
        ano = pd.to_numeric(base["ano"], errors="raise")
        periodo = pd.to_numeric(base["periodo"], errors="raise")
        valores = pd.to_numeric(base["valor_reais"], errors="raise")
    except (TypeError, ValueError) as erro:
        raise ValueError("Ano, período ou valor de despesa inválido.") from erro
    if (not np.isfinite(ano.to_numpy(dtype=float)).all()
            or not ano.between(2021, 2025).all()
            or not (ano % 1 == 0).all()):
        raise ValueError("Exercício fiscal inválido.")
    if (not np.isfinite(periodo.to_numpy(dtype=float)).all()
            or not periodo.eq(6).all()):
        raise ValueError("Apenas o sexto bimestre é admitido.")
    if not np.isfinite(valores.to_numpy(dtype=float)).all() or valores.lt(0).any():
        raise ValueError("Valores de despesa devem ser numéricos, finitos e não negativos.")
    if not base["uf"].isin(UF_IBGE).all():
        raise ValueError("O arquivo contém UF desconhecida.")
    if not base["funcao"].isin(FUNCOES).all():
        raise ValueError("Função de governo desconhecida.")
    codigos = base["funcao"].map(FUNCOES_CODIGO)
    if not base["codigo_funcao"].astype(str).str.zfill(2).eq(codigos).all():
        raise ValueError("Código incompatível com a função de governo.")
    if not base["cod_conta"].eq("RREO2TotalDespesas").all():
        raise ValueError("Os dados não pertencem ao quadro não intraorçamentário.")
    if not base["fonte_url"].apply(lambda x: isinstance(x, str) and x.startswith("https://")).all():
        raise ValueError("Fonte oficial não identificada.")
    for uf, nome in UF_IBGE.items():
        recortes = base["uf"].eq(uf)
        if recortes.any() and not base.loc[recortes, "estado"].eq(nome[1]).all():
            raise ValueError(f"Nome do estado incompatível com a UF {uf}.")
    base["ano"] = ano.astype(int)
    base["periodo"] = periodo.astype(int)
    base["valor_reais"] = valores.astype(float)
    if base.duplicated(subset=["uf", "ano", "funcao"]).any():
        raise ValueError("Existem registros duplicados para UF, ano e função.")
    return base.sort_values(["ano", "uf", "funcao"]).reset_index(drop=True)


def selecionar(base: pd.DataFrame, *, ano: int, ufs: list[str],
             funcoes: list[str]) -> pd.DataFrame:
    if not set(ufs).issubset(UF_IBGE) or not set(funcoes).issubset(FUNCOES):
        raise ValueError("Filtro de UF ou função inválido.")
    if not ufs or not funcoes:
        return base.iloc[0:0].copy()
    return base.loc[
        base["ano"].eq(ano) & base["uf"].isin(ufs) & base["funcao"].isin(funcoes)
    ].copy()


def agregar_ufs(base: pd.DataFrame, *, ano: int, ufs: list[str],
                funcoes: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Soma somente combinações completas; devolve separadamente as ausências."""
    filtrado = selecionar(base, ano=ano, ufs=ufs, funcoes=funcoes)
    linhas = []
    pendentes = []
    for uf in ufs:
        fatia = filtrado.loc[filtrado["uf"].eq(uf)]
        faltantes = [nome for nome in funcoes if nome not in set(fatia["funcao"])]
        if faltantes:
            pendentes.append({"uf": uf, "funcoes_ausentes": faltantes})
            continue
        linhas.append({
            "uf": uf, "estado": UF_IBGE[uf][1], "ano": ano,
            "valor_reais": float(fatia["valor_reais"].sum()),
            "funcoes_incluidas": len(funcoes),
        })
    colunas = ["uf", "estado", "ano", "valor_reais", "funcoes_incluidas"]
    resultado = pd.DataFrame(linhas, columns=colunas)
    return resultado.sort_values("valor_reais", ascending=False).reset_index(drop=True), pendentes


def composicao(base: pd.DataFrame, *, ano: int, uf: str) -> pd.DataFrame:
    """Percentuais da soma de três funções, NUNCA do orçamento total do governo."""
    fatia = selecionar(base, ano=ano, ufs=[uf], funcoes=list(FUNCOES))
    if set(fatia["funcao"]) != set(FUNCOES):
        return pd.DataFrame(columns=["uf", "funcao", "valor_reais", "participacao_pct"])
    total = float(fatia["valor_reais"].sum())
    fatia["participacao_pct"] = fatia["valor_reais"].mul(100).div(total) if total > 0 else np.nan
    return fatia[["uf", "funcao", "valor_reais", "participacao_pct"]].copy()


def comparar(base: pd.DataFrame, *, ano: int, uf_a: str, uf_b: str,
             funcoes: list[str]) -> dict:
    if uf_a == uf_b:
        raise ValueError("Escolha unidades da Federação diferentes.")
    calculos, pendencias = agregar_ufs(base, ano=ano, ufs=[uf_a, uf_b], funcoes=funcoes)
    if pendencias:
        raise ValueError("Não há dados completos para comparar: " +
                         "; ".join(p["uf"] + " (" + ", ".join(p["funcoes_ausentes"]) + ")"
                                   for p in pendencias))
    montantes = calculos.set_index("uf")["valor_reais"]
    a, b = float(montantes[uf_a]), float(montantes[uf_b])
    diferenca = b - a
    return {
        "uf_a": uf_a, "uf_b": uf_b, "valor_a": a, "valor_b": b,
        "diferenca_reais": diferenca,
        "diferenca_pct": (100 * diferenca / a) if a != 0 else None,
    }


def historico(base: pd.DataFrame, *, ufs: list[str], funcoes: list[str]) -> pd.DataFrame:
    """Séries por UF, omitindo anos incompletos; variação só entre anos contíguos."""
    linhas = []
    for ano in sorted(base["ano"].unique()):
        agregado, _ = agregar_ufs(base, ano=int(ano), ufs=ufs, funcoes=funcoes)
        linhas.extend(agregado[["uf", "estado", "ano", "valor_reais"]].to_dict("records"))
    saida = pd.DataFrame(linhas, columns=["uf", "estado", "ano", "valor_reais"])
    if saida.empty:
        saida["variacao_nominal_pct"] = pd.Series(dtype=float)
        return saida
    saida = saida.sort_values(["uf", "ano"]).reset_index(drop=True)
    saida["variacao_nominal_pct"] = np.nan
    for _, indice in saida.groupby("uf").groups.items():
        anteriores = None
        for i in indice:
            atual = saida.loc[i]
            if (anteriores is not None and atual["ano"] == anteriores["ano"] + 1
                    and anteriores["valor_reais"] != 0):
                saida.loc[i, "variacao_nominal_pct"] = (
                    100 * (atual["valor_reais"] / anteriores["valor_reais"] - 1)
                )
            anteriores = atual
    return saida


def descricao(agregados: pd.DataFrame) -> dict | None:
    """Descritivas sobre UFs completas, sem inferência estatística."""
    if agregados.empty:
        return None
    valores = agregados["valor_reais"]
    return {
        "quantidade_ufs": len(valores), "soma": float(valores.sum()),
        "media": float(valores.mean()), "mediana": float(valores.median()),
        "minimo": float(valores.min()), "maximo": float(valores.max()),
        "amplitude": float(valores.max() - valores.min()),
    }


def agregacao_regional(agregados: pd.DataFrame, selecionadas: list[str]) -> pd.DataFrame:
    """Total regional somente quando TODAS as UFs da região estão selecionadas e completas."""
    mapa = dict(zip(agregados["uf"], agregados["valor_reais"]))
    linhas = []
    for regiao, membros in REGIOES.items():
        faltantes = [uf for uf in membros if uf not in selecionadas or uf not in mapa]
        linhas.append({
            "regiao": regiao, "situacao": "completo" if not faltantes else "incompleto",
            "ufs_com_dados": sum(uf in mapa for uf in membros),
            "ufs_esperadas": len(membros), "ufs_ausentes": ", ".join(faltantes),
            "valor_reais": sum(mapa[uf] for uf in membros) if not faltantes else np.nan,
        })
    return pd.DataFrame(linhas)
