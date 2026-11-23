"""API REST. Execute: uvicorn api.main:app --reload"""
from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, status

from api.erros import configurar_erros
from api.routes.ia import router as ia_router
from api.routes.sumarizacao import router as sumarizacao_router
from api.routes.perguntas import router as perguntas_router
from api.schemas.geral import ConteudoWeb, ResumoEstatisticas, SaudeAPI
from api.routes.dados_oficiais import router as oficiais_router
from filelock import FileLock
from pydantic import BaseModel, ConfigDict, Field, model_validator

from utils.dados import (
    COLUNAS_MANUAIS, ESTADOS, FUNCOES,
    caminho_manuais, ler_web, listar_registros,
)

app = FastAPI(
    title="Transparência Brasil — API",
    description=(
        "Serviço local de consulta e comparação de despesas estaduais ilustrativas. "
        "A amostra original NÃO equivale a valores oficiais auditados. "
        "Cadastros via POST são mantidos separados e identificados como manuais."
    ),
    version="4.0.0",
)


configurar_erros(app)

app.include_router(ia_router)
app.include_router(sumarizacao_router)
app.include_router(perguntas_router)
app.include_router(oficiais_router)


class NovaDespesa(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    sigla: Literal["SP", "GO", "BA"] = Field(description="Estado da amostra")
    ano: int = Field(ge=2000, le=2100)
    funcao: Literal["Educação", "Saúde", "Segurança Pública"]
    valor_despesa: float = Field(ge=0, le=1e15, allow_inf_nan=False)
    populacao: int = Field(gt=0, le=300_000_000)


class RegistroDespesa(BaseModel):
    id_registro: str = Field(min_length=1)
    estado: str = Field(min_length=1)
    sigla: Literal["SP", "GO", "BA"]
    ano: int = Field(ge=2000, le=2100)
    funcao: Literal["Educação", "Saúde", "Segurança Pública"]
    valor_despesa: float = Field(ge=0, allow_inf_nan=False)
    populacao: int = Field(gt=0)
    fonte_fiscal: str = Field(min_length=1)
    fonte_populacao: str = Field(min_length=1)
    origem: Literal["amostra_academica", "manual"]
    data_cadastro: str | None = None


class RespostaDespesas(BaseModel):
    total: int = Field(ge=0)
    limite: int = Field(ge=1, le=1000)
    deslocamento: int = Field(ge=0)
    dados: list[RegistroDespesa]
    aviso: str = "A amostra é ilustrativa e não representa a totalidade das contas estaduais."


def _inserir_manual(registro: dict) -> None:
    """Protege gravações simultâneas e evita CSV parcialmente escrito."""
    destino = caminho_manuais()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(destino) + ".lock", timeout=15):
        registros = []
        if destino.exists():
            with destino.open(newline="", encoding="utf-8-sig") as arq:
                leitor = csv.DictReader(arq)
                if leitor.fieldnames and set(COLUNAS_MANUAIS) != set(leitor.fieldnames):
                    raise ValueError("O arquivo de registros manuais tem um formato inesperado")
                registros = list(leitor)
        registros.append(registro)
        fd, tmp = tempfile.mkstemp(prefix=".registros_", suffix=".csv", dir=destino.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as arq:
                escritor = csv.DictWriter(arq, fieldnames=COLUNAS_MANUAIS)
                escritor.writeheader()
                escritor.writerows(registros)
                arq.flush()
                os.fsync(arq.fileno())
            os.replace(tmp, destino)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


@app.get("/health", response_model=SaudeAPI, tags=["Sistema"])
def health():
    """Permite verificar se a API está em execução."""
    return {"status": "ok"}


@app.get("/despesas", response_model=RespostaDespesas, tags=["Despesas"])
def consultar_despesas(
    sigla: Literal["SP", "GO", "BA"] | None = None,
    ano: int | None = Query(default=None, ge=2000, le=2100),
    funcao: Literal["Educação", "Saúde", "Segurança Pública"] | None = None,
    origem: Literal["amostra_academica", "manual"] | None = None,
    limite: int = Query(default=100, ge=1, le=1000),
    deslocamento: int = Query(default=0, ge=0),
):
    """Lista registros com filtros, origem identificada e paginação."""
    registros = listar_registros()
    if sigla:
        registros = [r for r in registros if r["sigla"] == sigla]
    if ano is not None:
        registros = [r for r in registros if int(r["ano"]) == ano]
    if funcao:
        registros = [r for r in registros if r["funcao"] == funcao]
    if origem:
        registros = [r for r in registros if r["origem"] == origem]
    return {
        "total": len(registros), "limite": limite, "deslocamento": deslocamento,
        "dados": registros[deslocamento:deslocamento + limite],
    }


@app.post("/despesas", response_model=RegistroDespesa,
          status_code=status.HTTP_201_CREATED, tags=["Despesas"])
def cadastrar_despesa(nova: NovaDespesa):
    """Inclui um dado manual; NÃO altera `amostra_dados.csv`."""
    registro = {
        "estado": ESTADOS[nova.sigla], "sigla": nova.sigla,
        "ano": nova.ano, "funcao": nova.funcao,
        "valor_despesa": nova.valor_despesa, "populacao": nova.populacao,
        "fonte_fiscal": "Cadastro manual — não verificado",
        "fonte_populacao": "Cadastro manual — não verificado",
        "id_registro": "manual-" + uuid4().hex,
        "origem": "manual",
        "data_cadastro": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _inserir_manual(registro)
    return registro


@app.get("/estatisticas", response_model=ResumoEstatisticas, tags=["Análises"])
def estatisticas(origem: Literal["amostra_academica", "manual"] = "amostra_academica"):
    """Resumo por função, com origem explícita para não misturar amostra e cadastros."""
    registros = [r for r in listar_registros() if r["origem"] == origem]
    totais = {funcao: sum(float(r["valor_despesa"]) for r in registros
                          if r["funcao"] == funcao) for funcao in FUNCOES}
    return {
        "origem": origem, "quantidade": len(registros),
        "total_valor_despesa": sum(totais.values()),
        "totais_por_funcao": totais,
        "aviso": "Apenas registros locais da origem solicitada; não constitui total oficial estadual.",
    }


@app.get("/conteudo-web", response_model=list[ConteudoWeb], tags=["Conteúdo Web"])
def consultar_conteudo_web():
    """Retorna textos existentes no CSV, com URL de referência."""
    return ler_web().to_dict(orient="records")
