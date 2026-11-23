"""Contratos HTTP da sumarização automática e da síntese fiscal."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Modo = Literal["executivo", "topicos", "simplificado"]
Versao = Literal["basico", "estruturado", "fundamentado"]
Funcao = Literal["Educação", "Saúde", "Segurança Pública"]


class ConfiguracaoResumo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    modo: Modo = "executivo"
    versao_prompt: Versao = "fundamentado"
    max_novos_tokens: int = Field(default=384, ge=96, le=384)


class RequisicaoDocumento(ConfiguracaoResumo):
    documento_id: str = Field(pattern=r"^doc-[0-9a-f]{20}$", min_length=24, max_length=24)


class RequisicaoFiscal(ConfiguracaoResumo):
    ufs: list[str] = Field(min_length=1, max_length=27)
    ano: int = Field(ge=2021, le=2025)
    funcoes: list[Funcao] = Field(
        default_factory=lambda: ["Educação", "Saúde", "Segurança Pública"],
        min_length=1, max_length=3,
    )

    @field_validator("ufs")
    @classmethod
    def validar_ufs(cls, valor: list[str]) -> list[str]:
        from services.siconfi import UF_IBGE
        if len(set(valor)) != len(valor) or any(uf not in UF_IBGE for uf in valor):
            raise ValueError("Lista de UFs inválida ou repetida.")
        return valor

    @field_validator("funcoes")
    @classmethod
    def validar_funcoes(cls, valor: list[str]) -> list[str]:
        if len(set(valor)) != len(valor):
            raise ValueError("Funções repetidas.")
        return valor


class DocumentoCatalogado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    titulo: str
    url: str
    data_coleta: str
    metodo: str
    origem: str
    caracteres: int = Field(ge=1)


class RespostaSumarizacao(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo: Literal["documento", "fiscal"]
    titulo: str = Field(min_length=1)
    resultado: str = Field(min_length=1)
    modo: Modo
    versao_prompt: Versao
    modelo: str = Field(min_length=1)
    execucao_local: Literal[True]
    etapas_geracao: int = Field(ge=1)
    tokens_entrada: int = Field(ge=1)
    tokens_saida: int = Field(ge=1)
    tempo_processamento_ms: int = Field(ge=0)
    fontes: list[str]
    metadados: dict[str, str | int]
    contexto_calculado: str | None = None
    aviso: str = Field(min_length=1)
