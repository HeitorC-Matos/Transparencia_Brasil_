"""Modelos Pydantic de resposta para consultas locais da aplicação.

Não alteram os JSONs consumidos atualmente pelo Streamlit; documentam e
validam os campos que já eram retornados pela API.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.dados import FUNCOES


ValorNaoNegativo = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Funcao = Literal["Educação", "Saúde", "Segurança Pública"]


class SaudeAPI(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]


class ResumoEstatisticas(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    origem: Literal["amostra_academica", "manual"]
    quantidade: int = Field(ge=0)
    total_valor_despesa: ValorNaoNegativo
    totais_por_funcao: dict[Funcao, ValorNaoNegativo] = Field(
        description="Despesas por função na origem solicitada; não representa o total estadual."
    )
    aviso: str = Field(min_length=1)

    @field_validator("totais_por_funcao")
    @classmethod
    def exigir_tres_funcoes(cls, valores: dict) -> dict:
        if set(valores) != set(FUNCOES):
            raise ValueError("A resposta deve conter exatamente as três funções da amostra.")
        return valores


class ConteudoWeb(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=1)
    url: str = Field(min_length=1, max_length=2048, pattern=r"^https?://")
    texto: str = Field(min_length=1)
    data_coleta: str = Field(min_length=1)
    metodo: str = Field(min_length=1)
