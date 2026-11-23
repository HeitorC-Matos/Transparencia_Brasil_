"""Indicadores verificáveis do dashboard: sem inferência de LLM nem dados ilustrativos.

As funções recebem exclusivamente os registros oficiais validados vindos da API.
Um subtotal só inclui UFs que possuem todas as funções exigidas no recorte.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.estatisticas_oficiais import agregar_ufs, historico, selecionar


@dataclass(frozen=True)
class VisaoDashboard:
    ano: int
    ufs_solicitadas: tuple[str, ...]
    funcoes: tuple[str, ...]
    recorte: pd.DataFrame
    ranking: pd.DataFrame
    totais_funcao: pd.DataFrame
    serie_historica: pd.DataFrame
    pendencias: list[dict]
    cobertura: int
    combinacoes_esperadas: int
    fontes: tuple[str, ...]

    @property
    def soma(self) -> float | None:
        """None quando não há UFs completas; zero real continua sendo zero."""
        if self.ranking.empty:
            return None
        return float(self.ranking["valor_reais"].sum())

    @property
    def ufs_completas(self) -> list[str]:
        return self.ranking["uf"].tolist()


def montar_visao(base: pd.DataFrame, *, ano: int, ufs: list[str],
                 funcoes: list[str], ufs_historico: list[str] | None = None) -> VisaoDashboard:
    """Reutiliza os mesmos critérios contábeis e agregações da página Estatísticas."""
    if not ufs or not funcoes:
        raise ValueError("Selecione ao menos uma UF e uma função.")
    if len(set(ufs)) != len(ufs) or len(set(funcoes)) != len(funcoes):
        raise ValueError("Seleções repetidas de UF ou função.")
    if ano not in {int(a) for a in base["ano"].unique()}:
        raise ValueError("O exercício não está disponível na base oficial.")
    recorte = selecionar(base, ano=ano, ufs=ufs, funcoes=funcoes)
    ranking, pendencias = agregar_ufs(base, ano=ano, ufs=ufs, funcoes=funcoes)
    completas = ranking["uf"].tolist()
    computaveis = recorte.loc[recorte["uf"].isin(completas)]
    totais = (
        computaveis.groupby("funcao", as_index=False)["valor_reais"].sum()
        if not computaveis.empty else pd.DataFrame(columns=["funcao", "valor_reais"])
    )
    # Série individual mantém a regra de não preencher anos/UFs incompletos.
    historicas = list(ufs_historico) if ufs_historico is not None else ufs[:3]
    if any(uf not in ufs for uf in historicas):
        raise ValueError("O histórico deve conter apenas UFs selecionadas no painel.")
    serie = historico(base, ufs=historicas, funcoes=funcoes) if historicas else pd.DataFrame()
    fontes = tuple(sorted(set(recorte["fonte_url"].dropna().tolist())))
    return VisaoDashboard(
        ano=ano, ufs_solicitadas=tuple(ufs), funcoes=tuple(funcoes),
        recorte=recorte, ranking=ranking, totais_funcao=totais,
        serie_historica=serie, pendencias=pendencias, cobertura=len(recorte),
        combinacoes_esperadas=len(ufs) * len(funcoes), fontes=fontes,
    )


def chave_recorte(ano: int, ufs: list[str], funcoes: list[str]) -> tuple:
    """Identifica a seleção para impedir que uma resposta de IA pareça atual após mudar filtros."""
    return int(ano), tuple(sorted(ufs)), tuple(sorted(funcoes))
