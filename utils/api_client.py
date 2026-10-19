"""Cliente HTTP real utilizado pelas páginas Streamlit para consumir FastAPI.

Endereço configurável: TP3_API_URL (padrão http://127.0.0.1:8000).
O cliente NÃO importa a aplicação FastAPI e NÃO lê CSVs internamente.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests


class APIIndisponivel(RuntimeError):
    """Erro de conexão, status HTTP ou contrato inesperado da API."""


def base_url() -> str:
    return os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")


def requisitar(metodo: str, caminho: str, *, parametros: dict | None = None,
               json: dict | None = None, sessao=None) -> Any:
    """Faz a chamada HTTP; sessão injetável permite testes sem Internet."""
    cliente = sessao if sessao is not None else requests
    url = f"{base_url()}{caminho}"
    try:
        if metodo.upper() == "GET":
            resposta = cliente.get(url, params=parametros, timeout=8)
        elif metodo.upper() == "POST":
            resposta = cliente.post(url, json=json, timeout=8)
        else:
            raise ValueError("Método HTTP não suportado")
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        raise APIIndisponivel(f"{metodo.upper()} {caminho}: {erro}") from erro


def verificar_api(*, sessao=None) -> bool:
    try:
        resposta = requisitar("GET", "/health", sessao=sessao)
        return resposta.get("status") == "ok"
    except (APIIndisponivel, AttributeError):
        return False


def consultar_despesas(*, sigla: str | None = None, ano: int | None = None,
                       funcao: str | None = None, origem: str | None = "amostra_academica",
                       sessao=None) -> pd.DataFrame:
    """Busca TODAS as páginas paginadas por HTTP, sem perder registros."""
    filtros = {k: v for k, v in {
        "sigla": sigla, "ano": ano, "funcao": funcao, "origem": origem,
    }.items() if v is not None}
    registros: list[dict] = []
    deslocamento = 0
    while True:
        resposta = requisitar(
            "GET", "/despesas", parametros={**filtros, "limite": 1000,
                                              "deslocamento": deslocamento}, sessao=sessao
        )
        if not isinstance(resposta, dict) or not isinstance(resposta.get("dados"), list):
            raise APIIndisponivel("Resposta de /despesas fora do formato esperado")
        lote = resposta["dados"]
        registros.extend(lote)
        deslocamento += len(lote)
        try:
            total = int(resposta["total"])
        except (ValueError, KeyError, TypeError) as erro:
            raise APIIndisponivel("Total inválido retornado por /despesas") from erro
        if deslocamento >= total:
            break
        if not lote:
            raise APIIndisponivel("Paginação incompleta na API")
    resultado = pd.DataFrame(registros)
    for campo in ("ano", "populacao", "valor_despesa"):
        if campo in resultado.columns:
            resultado[campo] = pd.to_numeric(resultado[campo], errors="raise")
    return resultado


def consultar_estatisticas(*, origem: str = "amostra_academica", sessao=None) -> dict:
    resultado = requisitar("GET", "/estatisticas", parametros={"origem": origem}, sessao=sessao)
    if not isinstance(resultado, dict) or "total_valor_despesa" not in resultado:
        raise APIIndisponivel("Estatísticas inválidas retornadas pela API")
    return resultado


def cadastrar_despesa(registro: dict, *, sessao=None) -> dict:
    resposta = requisitar("POST", "/despesas", json=registro, sessao=sessao)
    if not isinstance(resposta, dict) or resposta.get("origem") != "manual":
        raise APIIndisponivel("Resposta de cadastro inesperada")
    return resposta


def consultar_conteudo_web(*, sessao=None) -> pd.DataFrame:
    registros = requisitar("GET", "/conteudo-web", sessao=sessao)
    if not isinstance(registros, list):
        raise APIIndisponivel("Conteúdo Web fora do formato esperado")
    return pd.DataFrame(registros)
