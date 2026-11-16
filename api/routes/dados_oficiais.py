"""Rotas isoladas para informações declaratórias do Siconfi."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.consulta_oficial import BaseOficialInvalida, agregar_regioes, filtrar, serie, status_base
from services.siconfi import FUNCOES_CODIGO, UF_ORDENADAS

router = APIRouter(prefix="/dados-oficiais", tags=["Dados oficiais — Siconfi"])
UF = Literal[tuple(UF_ORDENADAS)]
Funcao = Literal["Educação", "Saúde", "Segurança Pública"]


class DespesaOficial(BaseModel):
    uf: str
    estado: str
    ano: int
    funcao: str
    codigo_funcao: str
    valor_reais: Decimal = Field(ge=0)
    estagio: str
    periodo: int
    anexo: str
    cod_conta: str
    abrangencia: str
    origem: str
    fonte_url: str
    data_coleta_utc: str
    hash_fonte_sha256: str


class RespostaOficial(BaseModel):
    total: int = Field(ge=0)
    limite: int = Field(ge=1)
    deslocamento: int = Field(ge=0)
    dados: list[DespesaOficial]
    aviso: str


class StatusOficial(BaseModel):
    situacao: str
    registros_validados: int
    combinacoes_validas: int
    total_combinacoes: int
    ufs: list[str]
    anos: list[int]
    combinacoes_pendentes: list[dict]
    gerado_em_utc: str | None = None
    criterio: str | None = None
    fonte: str | None = None


class PontoSerie(BaseModel):
    uf: str
    ano: int
    funcao: str
    valor_reais: Decimal = Field(ge=0)
    variacao_nominal_percentual: Decimal | None = None
    fonte_url: str


class RespostaSerie(BaseModel):
    uf: str
    funcao: str
    dados: list[PontoSerie]
    aviso: str


@router.get("/status", response_model=StatusOficial)
def situacao_oficial():
    try:
        return status_base()
    except BaseOficialInvalida as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro


@router.get("", response_model=RespostaOficial)
def consultar_dados_oficiais(
    uf: UF | None = None,
    ano: int | None = Query(default=None, ge=2021, le=2025),
    funcao: Funcao | None = None,
    limite: int = Query(default=100, ge=1, le=1000),
    deslocamento: int = Query(default=0, ge=0),
):
    try:
        registros = filtrar(uf=uf, ano=ano, funcao=funcao)
    except BaseOficialInvalida as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
    return {
        "total": len(registros), "limite": limite, "deslocamento": deslocamento,
        "dados": registros[deslocamento: deslocamento + limite],
        "aviso": (
            "Valores declarados ao Siconfi, RREO Anexo 02, liquidados acumulados do 6º bimestre; "
            "excluídas despesas intraorçamentárias. Comparação entre governos estaduais/distrital, "
            "não inclui despesas municipais. Sem auditoria independente; valores nominais."
        ),
    }


class GrupoRegional(BaseModel):
    regiao: str
    ano: int
    funcao: str
    ufs_esperadas: int
    ufs_com_dados: int
    ufs_ausentes: list[str]
    valor_reais: Decimal | None
    situacao: Literal["completo", "incompleto"]


class RespostaRegioes(BaseModel):
    dados: list[GrupoRegional]
    aviso: str


@router.get("/regioes", response_model=RespostaRegioes)
def consultar_regioes(ano: int = Query(ge=2021, le=2025), funcao: Funcao = Query()):
    try:
        dados = agregar_regioes(ano=ano, funcao=funcao)
    except BaseOficialInvalida as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
    return {
        "dados": dados,
        "aviso": "Totais regionais exibidos somente quando todas as UFs da região possuem dados validados.",
    }


@router.get("/serie", response_model=RespostaSerie)
def consultar_serie(uf: UF, funcao: Funcao):
    try:
        dados = serie(uf, funcao)
    except BaseOficialInvalida as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
    return {
        "uf": uf, "funcao": funcao, "dados": dados,
        "aviso": "Variações nominais calculadas apenas para exercícios consecutivos com base anterior não nula.",
    }
