"""Contratos de entrada e saída para a inferência local.

A validação estrutural assegura formato, tipos e limites; não atesta a
veracidade do conteúdo gerado pelo modelo de linguagem.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequisicaoTexto(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, str_strip_whitespace=True,
        json_schema_extra={"examples": [{
            "texto": "A transparência facilita o acompanhamento das despesas públicas.",
            "operacao": "resumo", "max_novos_tokens": 128,
        }]},
    )

    texto: str = Field(
        min_length=1, max_length=12000,
        description="Conteúdo textual a ser resumido ou explicado pelo Qwen local.",
    )
    operacao: Literal["resumo", "explicacao"] = Field(
        default="resumo", description="Operação de linguagem natural solicitada."
    )
    max_novos_tokens: int = Field(
        default=384, ge=32, le=512,
        description="Número máximo de novos tokens; faixa: 32 a 512."
    )

    @field_validator("texto")
    @classmethod
    def exigir_conteudo_textual(cls, valor: str) -> str:
        # Um texto só de espaços, pontuação ou caracteres invisíveis não
        # constitui entrada útil para uma operação de resumo/explicação.
        if not any(caractere.isalnum() for caractere in valor):
            raise ValueError("Informe um texto com conteúdo legível.")
        return valor


class RespostaTexto(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    operacao: Literal["resumo", "explicacao"] = Field(description="Operação efetivamente realizada.")
    texto_original: str = Field(min_length=1, max_length=12000)
    resultado: str = Field(min_length=1, max_length=30000,
                          description="Resposta textual não vazia produzida pelo Qwen.")
    modelo: str = Field(min_length=1, max_length=200)
    execucao_local: Literal[True] = Field(description="Confirma a configuração de inferência local.")
    tokens_entrada: int = Field(ge=1, description="Tokens do prompt completo, incluindo instruções.")
    tokens_saida: int = Field(ge=1, description="Tokens efetivamente gerados pelo modelo.")
    tempo_processamento_ms: int = Field(ge=0, description="Tempo medido no backend em milissegundos.")
    aviso: str = Field(min_length=1, max_length=500)


class StatusModelo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    status: Literal["carregado", "nao_carregado", "arquivos_ausentes", "erro_carregamento"]
    modelo: str = Field(min_length=1, max_length=200)
    execucao_local: Literal[True]
    caminho_modelo: str = Field(min_length=1, max_length=4096)
    detalhe: str = Field(min_length=1, max_length=500)
