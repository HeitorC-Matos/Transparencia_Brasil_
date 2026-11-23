"""Leitura centralizada das fontes do projeto, sem inventar registros oficiais."""
from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUNAS_GASTOS = (
    "estado", "sigla", "ano", "funcao", "valor_despesa", "populacao",
    "fonte_fiscal", "fonte_populacao",
)
COLUNAS_MANUAIS = COLUNAS_GASTOS + ("id_registro", "origem", "data_cadastro")
COLUNAS_WEB = ("titulo", "url", "texto")
ESTADOS = {"SP": "São Paulo", "GO": "Goiás", "BA": "Bahia"}
FUNCOES = ("Educação", "Saúde", "Segurança Pública")


def pasta_dados() -> Path:
    """A variável TP3_DATA_DIR permite testes isolados sem mexer nos arquivos originais."""
    return Path(os.environ.get("TP3_DATA_DIR", str(ROOT / "data"))).resolve()


def caminho_amostra() -> Path:
    return pasta_dados() / "amostra_dados.csv"


def caminho_web() -> Path:
    return pasta_dados() / "conteudo_web.csv"


def caminho_manuais() -> Path:
    return pasta_dados() / "registros_manuais.csv"


def ler_amostra() -> pd.DataFrame:
    caminho = caminho_amostra()
    if not caminho.is_file():
        raise FileNotFoundError(f"Base de demonstração não encontrada: {caminho}")
    df = pd.read_csv(caminho, encoding="utf-8-sig", dtype={"sigla": str})
    faltantes = set(COLUNAS_GASTOS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes na amostra: {', '.join(sorted(faltantes))}")
    for coluna in ("ano", "valor_despesa", "populacao"):
        df[coluna] = pd.to_numeric(df[coluna], errors="raise")
    return df.loc[:, COLUNAS_GASTOS].copy()


def ler_web() -> pd.DataFrame:
    """Catálogo das fontes do Beautiful Soup + Selenium (se houver CSV válido)."""
    quadros = []
    for caminho in (caminho_web(), pasta_dados() / "conteudo_selenium.csv"):
        if not caminho.exists():
            continue
        df = pd.read_csv(caminho, encoding="utf-8-sig").fillna("")
        faltantes = set(COLUNAS_WEB) - set(df.columns)
        if faltantes:
            raise ValueError(f"Colunas ausentes em {caminho.name}: {', '.join(sorted(faltantes))}")
        quadros.append(df)
    if not quadros:
        return pd.DataFrame(columns=COLUNAS_WEB)
    # Caso uma fonte esteja em ambos os arquivos, prevalece a coleta Selenium.
    return pd.concat(quadros, ignore_index=True).drop_duplicates(subset="url", keep="last")


def ler_manuais() -> list[dict]:
    caminho = caminho_manuais()
    if not caminho.exists():
        return []
    with caminho.open(newline="", encoding="utf-8-sig") as arq:
        leitor = csv.DictReader(arq)
        if leitor.fieldnames is None:
            return []
        faltantes = set(COLUNAS_MANUAIS) - set(leitor.fieldnames)
        if faltantes:
            raise ValueError("CSV manual está incompleto: " + ", ".join(sorted(faltantes)))
        return list(leitor)


def listar_registros() -> list[dict]:
    """Normaliza amostra e cadastros separadamente identificando cada origem."""
    registros = []
    for indice, row in ler_amostra().iterrows():
        registro = row.to_dict()
        registro["id_registro"] = f"amostra-{indice + 1:03d}"
        registro["origem"] = "amostra_academica"
        registro["data_cadastro"] = None
        registros.append(registro)
    for row in ler_manuais():
        registro = dict(row)
        registro["ano"] = int(registro["ano"])
        registro["populacao"] = int(registro["populacao"])
        registro["valor_despesa"] = float(registro["valor_despesa"])
        registros.append(registro)
    return registros
