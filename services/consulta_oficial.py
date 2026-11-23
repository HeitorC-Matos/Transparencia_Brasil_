"""Consultas locais à base fiscal validada, sem rede e sem misturar amostra."""
from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation

from services.siconfi import CAMPOS_EXPORTADOS, UF_IBGE, FUNCOES_CODIGO, REGIOES, diretorio_siconfi


class BaseOficialInvalida(ValueError):
    pass


def status_base() -> dict:
    destino = diretorio_siconfi()
    caminho = destino / "manifesto.json"
    if not caminho.is_file():
        return {"situacao": "nao_coletado", "registros_validados": 0,
                "combinacoes_validas": 0, "total_combinacoes": 0,
                "ufs": [], "anos": [], "combinacoes_pendentes": [], "gerado_em_utc": None,
                "criterio": None, "fonte": None}
    try:
        info = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(info, dict):
            raise ValueError("manifesto inesperado")
        return info
    except (OSError, ValueError) as erro:
        raise BaseOficialInvalida("Manifesto de dados oficiais ilegível") from erro


def ler_oficiais() -> list[dict]:
    arquivo = diretorio_siconfi() / "despesas_oficiais.csv"
    if not arquivo.exists():
        return []
    saida: list[dict] = []
    vistos: set[tuple[str, int, str]] = set()
    try:
        with arquivo.open(encoding="utf-8-sig", newline="") as arq:
            leitor = csv.DictReader(arq)
            if leitor.fieldnames is None or set(CAMPOS_EXPORTADOS) - set(leitor.fieldnames):
                raise BaseOficialInvalida("CSV oficial com colunas ausentes")
            for linha in leitor:
                uf, funcao = linha["uf"], linha["funcao"]
                ano = int(linha["ano"])
                valor = Decimal(linha["valor_reais"])
                if (uf not in UF_IBGE or funcao not in FUNCOES_CODIGO or not 2021 <= ano <= 2025
                        or linha["codigo_funcao"] != FUNCOES_CODIGO[funcao]
                        or valor < 0 or not valor.is_finite()
                        or linha["periodo"] != "6"
                        or linha["cod_conta"] != "RREO2TotalDespesas"):
                    raise BaseOficialInvalida("Registro oficial não atende ao padrão contábil")
                chave = (uf, ano, funcao)
                if chave in vistos:
                    raise BaseOficialInvalida("Duplicidade de UF/ano/função no CSV")
                vistos.add(chave)
                linha["ano"] = ano
                linha["periodo"] = 6
                linha["valor_reais"] = valor
                saida.append(linha)
        return saida
    except (OSError, ValueError, InvalidOperation) as erro:
        if isinstance(erro, BaseOficialInvalida):
            raise
        raise BaseOficialInvalida("Base oficial inválida ou ilegível") from erro


def filtrar(*, uf: str | None = None, ano: int | None = None,
            funcao: str | None = None) -> list[dict]:
    return [r for r in ler_oficiais()
            if (uf is None or r["uf"] == uf)
            and (ano is None or r["ano"] == ano)
            and (funcao is None or r["funcao"] == funcao)]


def serie(uf: str, funcao: str) -> list[dict]:
    base = sorted(filtrar(uf=uf, funcao=funcao), key=lambda r: r["ano"])
    ultimo = None
    resultado = []
    for registro in base:
        valor = registro["valor_reais"]
        # Variações só entre exercícios consecutivos; zero impede divisão.
        variacao = None
        if ultimo is not None and ultimo["ano"] + 1 == registro["ano"] and ultimo["valor_reais"] != 0:
            variacao = (valor / ultimo["valor_reais"] - Decimal(1)) * Decimal(100)
        resultado.append({
            "uf": uf, "ano": registro["ano"], "funcao": funcao,
            "valor_reais": valor, "variacao_nominal_percentual": (
                round(variacao, 4) if variacao is not None else None
            ), "fonte_url": registro["fonte_url"],
        })
        ultimo = registro
    return resultado


def agregar_regioes(ano: int, funcao: str) -> list[dict]:
    """Não publica totais de uma região quando faltam UFs no mesmo exercício."""
    dados = filtrar(ano=ano, funcao=funcao)
    mapa = {r["uf"]: r["valor_reais"] for r in dados}
    resultado = []
    for regiao, membros in REGIOES.items():
        presentes = [uf for uf in membros if uf in mapa]
        ausentes = [uf for uf in membros if uf not in mapa]
        resultado.append({
            "regiao": regiao, "ano": ano, "funcao": funcao,
            "ufs_esperadas": len(membros), "ufs_com_dados": len(presentes),
            "ufs_ausentes": ausentes,
            "valor_reais": sum((mapa[uf] for uf in presentes), Decimal(0)) if not ausentes else None,
            "situacao": "completo" if not ausentes else "incompleto",
        })
    return resultado
