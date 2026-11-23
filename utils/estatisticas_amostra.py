"""Indicadores comparativos da AMOSTRA ILUSTRATIVA (sem dados oficiais).

O denominador das participações é SOMENTE a soma das funções presentes
na amostra de cada estado/ano; não é o orçamento total do governo.
Todas as funções são puras e não alteram DataFrames recebidos.
"""
from __future__ import annotations

import math

import pandas as pd

COLUNAS = ("estado", "sigla", "ano", "funcao", "valor_despesa", "populacao")


def validar_amostra(df: pd.DataFrame) -> pd.DataFrame:
    """Valida tipos, consistência populacional e unicidade estado/ano/função."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("A base de despesas não está em formato tabular.")
    faltam = set(COLUNAS).difference(df.columns)
    if faltam:
        raise ValueError("A amostra não possui as colunas: " + ", ".join(sorted(faltam)))
    if df.empty:
        return df.copy()
    dados = df.copy()
    for campo in ("estado", "sigla", "funcao"):
        if dados[campo].isna().any():
            raise ValueError(f"Existem valores ausentes no campo {campo}.")
        dados[campo] = dados[campo].astype(str).str.strip()
        if dados[campo].eq("").any():
            raise ValueError(f"Existem valores vazios no campo {campo}.")
    for campo in ("ano", "valor_despesa", "populacao"):
        try:
            dados[campo] = pd.to_numeric(dados[campo], errors="raise")
        except (TypeError, ValueError) as erro:
            raise ValueError(f"Valores não numéricos no campo {campo}.") from erro
        if not dados[campo].map(lambda x: math.isfinite(float(x))).all():
            raise ValueError(f"Existem valores ausentes ou infinitos no campo {campo}.")
    if (dados["ano"] % 1 != 0).any():
        raise ValueError("Os exercícios da amostra devem ser números inteiros.")
    dados["ano"] = dados["ano"].astype(int)
    if (dados["valor_despesa"] < 0).any():
        raise ValueError("A amostra possui despesas negativas e exige conferência.")
    if (dados["populacao"] <= 0).any() or (dados["populacao"] % 1 != 0).any():
        raise ValueError("A população deve ser um inteiro positivo.")
    dados["populacao"] = dados["populacao"].astype("int64")
    if dados.duplicated(["sigla", "ano", "funcao"]).any():
        raise ValueError("Existem registros duplicados para o mesmo estado, ano e função.")
    por_estado = dados.groupby(["sigla", "ano"], dropna=False)
    if (por_estado["populacao"].nunique() != 1).any():
        raise ValueError("Há populações diferentes para o mesmo estado e exercício.")
    if (por_estado["estado"].nunique() != 1).any():
        raise ValueError("Há nomes diferentes para a mesma sigla e exercício.")
    if (dados.groupby("estado")["sigla"].nunique() != 1).any():
        raise ValueError("O mesmo estado aparece com diferentes siglas.")
    return dados


def resumo_estados(df: pd.DataFrame, funcao: str | None = None) -> pd.DataFrame:
    """Soma das funções selecionadas e despesa por habitante para cada UF."""
    dados = validar_amostra(df)
    if funcao is not None:
        dados = dados.loc[dados["funcao"].eq(funcao)].copy()
    if dados.empty:
        return pd.DataFrame(columns=["estado", "sigla", "ano", "total", "populacao", "valor_por_habitante", "funcoes"])
    resultado = dados.groupby(["estado", "sigla", "ano"], as_index=False).agg(
        total=("valor_despesa", "sum"),
        populacao=("populacao", "first"),
        funcoes=("funcao", "nunique"),
    )
    resultado["valor_por_habitante"] = resultado["total"] / resultado["populacao"]
    return resultado.sort_values(["estado", "ano"]).reset_index(drop=True)


def composicao_funcoes(df: pd.DataFrame) -> pd.DataFrame:
    """Participação no total das funções disponíveis em cada estado, NÃO no orçamento."""
    dados = validar_amostra(df)
    if dados.empty:
        return pd.DataFrame(columns=["estado", "sigla", "ano", "funcao", "valor_despesa", "total_selecionado", "participacao_pct"])
    resultado = dados.groupby(["estado", "sigla", "ano", "funcao"], as_index=False)["valor_despesa"].sum()
    resultado["total_selecionado"] = resultado.groupby(["sigla", "ano"])["valor_despesa"].transform("sum")
    resultado["participacao_pct"] = (
        resultado["valor_despesa"]
        .div(resultado["total_selecionado"].replace(0, float("nan"))) * 100
    )
    return resultado.sort_values(["estado", "funcao"]).reset_index(drop=True)


def per_capita_funcoes(df: pd.DataFrame) -> pd.DataFrame:
    """Despesa por pessoa por função, usando população uma vez por UF/ano."""
    dados = validar_amostra(df)
    resultado = dados.loc[:, ["estado", "sigla", "ano", "funcao", "valor_despesa", "populacao"]].copy()
    resultado["valor_por_habitante"] = resultado["valor_despesa"] / resultado["populacao"]
    return resultado.sort_values(["estado", "funcao"]).reset_index(drop=True)


def classificar_estados(df: pd.DataFrame, *, funcao: str | None = None,
                       criterio: str = "total") -> pd.DataFrame:
    """Ranking descritivo por valor absoluto ou habitante (não é ranking de gestão)."""
    if criterio not in ("total", "valor_por_habitante"):
        raise ValueError("Critério de classificação desconhecido.")
    tabela = resumo_estados(df, funcao)
    tabela = tabela.sort_values([criterio, "estado"], ascending=[False, True]).reset_index(drop=True)
    tabela.insert(0, "posicao", range(1, len(tabela) + 1))
    return tabela


def comparar_estados(df: pd.DataFrame, estado_a: str, estado_b: str,
                     *, funcao: str | None = None) -> dict:
    """Diferenças B − A, percentuais sempre relativos a A, se A for não zero."""
    if estado_a == estado_b:
        raise ValueError("Selecione dois estados diferentes para comparar.")
    tabela = resumo_estados(df, funcao)
    selecao_a = tabela[tabela["estado"].eq(estado_a)]
    selecao_b = tabela[tabela["estado"].eq(estado_b)]
    if len(selecao_a) != 1 or len(selecao_b) != 1:
        raise ValueError("Cada estado deve ter exatamente um conjunto de dados no exercício selecionado.")
    a, b = selecao_a.iloc[0], selecao_b.iloc[0]
    if int(a["ano"]) != int(b["ano"]):
        raise ValueError("Não é possível comparar estados de exercícios diferentes.")
    def variacao(valor_a: float, valor_b: float) -> dict:
        absoluto = float(valor_b) - float(valor_a)
        relativo = (absoluto / float(valor_a) * 100) if valor_a != 0 else None
        return {"a": float(valor_a), "b": float(valor_b),
                "diferenca": absoluto, "diferenca_pct": relativo}
    return {
        "estado_a": estado_a, "estado_b": estado_b, "ano": int(a["ano"]),
        "funcao": funcao or "Todas as funções da amostra",
        "valor_absoluto": variacao(a["total"], b["total"]),
        "por_habitante": variacao(a["valor_por_habitante"], b["valor_por_habitante"]),
    }


def estatisticas_por_funcao(df: pd.DataFrame) -> pd.DataFrame:
    """Média/mediana e dispersão DESCRITIVA dos valores entre estados, por função."""
    dados = validar_amostra(df)
    if dados.empty:
        return pd.DataFrame(columns=["funcao", "estados", "media", "mediana", "minimo", "maximo", "amplitude"])
    agrupado = dados.groupby("funcao", as_index=False).agg(
        estados=("sigla", "nunique"),
        media=("valor_despesa", "mean"),
        mediana=("valor_despesa", "median"),
        minimo=("valor_despesa", "min"),
        maximo=("valor_despesa", "max"),
    )
    agrupado["amplitude"] = agrupado["maximo"] - agrupado["minimo"]
    return agrupado.sort_values("funcao").reset_index(drop=True)


def matriz_funcoes(df: pd.DataFrame, metrica: str = "valor_despesa") -> pd.DataFrame:
    """Matriz estado × função; dados ausentes ficam ausentes (nunca zero inventado)."""
    if metrica not in ("valor_despesa", "valor_por_habitante"):
        raise ValueError("Métrica desconhecida.")
    dados = per_capita_funcoes(df)
    if dados.empty:
        return pd.DataFrame()
    return dados.pivot(index="estado", columns="funcao", values=metrica).sort_index()
