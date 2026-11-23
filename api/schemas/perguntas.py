"""Contratos HTTP: perguntas em linguagem natural com respostas calculadas pelo Python."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequisicaoPergunta(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    pergunta: str = Field(min_length=5, max_length=500)
    ano_referencia: int = Field(default=2025, ge=2021, le=2025)
    usar_qwen: bool = True
    max_novos_tokens: int = Field(default=384, ge=96, le=384)

    @field_validator("pergunta")
    @classmethod
    def sem_branco(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A pergunta não pode ficar em branco.")
        return valor


class RegistroConsultado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uf: str = Field(min_length=2, max_length=2)
    estado: str = Field(min_length=2)
    ano: int = Field(ge=2021, le=2025)
    funcao: Literal["Educação", "Saúde", "Segurança Pública"]
    valor_reais: Decimal = Field(ge=0)
    fonte_url: str = Field(min_length=1)
    posicao: int | None = Field(default=None, ge=1)
    variacao_nominal_percentual: Decimal | None = None
    participacao_percentual: Decimal | None = Field(default=None, ge=0, le=100)


class RespostaPergunta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["ranking", "consulta", "comparacao", "evolucao", "participacao", "ods16"]
    pergunta_interpretada: str = Field(min_length=1)
    resposta_calculada: str = Field(min_length=1)
    dados: list[RegistroConsultado]
    fontes: list[str] = Field(min_length=1)
    criterio: str = Field(min_length=1)
    observacoes: list[str]
    explicacao_ia: str | None = None
    qwen_executado: bool = False
    modelo: str | None = None
    aviso_ia: str | None = None
    tokens_entrada: int | None = Field(default=None, ge=1)
    tokens_saida: int | None = Field(default=None, ge=1)
    tempo_processamento_ms: int | None = Field(default=None, ge=0)
