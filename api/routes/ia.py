"""Processamento de linguagem natural com modelo residente no computador."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from api.erros import RespostaErro

from api.schemas.ia import RequisicaoTexto, RespostaTexto, StatusModelo
from services.llm_service import (
    MODEL_ID, MemoriaInsuficiente, ModeloIndisponivel, ModeloOcupado,
    TempoLimiteGeracao, TextoMuitoLongo, servico_llm,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["IA local"])


@router.get("/ia/health", response_model=StatusModelo)
def estado_modelo():
    """Informa o estado do modelo sem iniciar um carregamento de vários gigabytes."""
    return servico_llm.status()


@router.post(
    "/processar_texto", response_model=RespostaTexto,
    responses={
        422: {"model": RespostaErro, "description": "Entrada inválida ou texto longo"},
        429: {"model": RespostaErro, "description": "Modelo ocupado; consulte Retry-After"},
        500: {"model": RespostaErro, "description": "Falha interna ou resposta inválida"},
        503: {"model": RespostaErro, "description": "Modelo indisponível ou GPU sem memória"},
        504: {"model": RespostaErro, "description": "Tempo limite de processamento"},
    },
)
def processar_texto(requisicao: RequisicaoTexto):
    """Gera resumo/explicação diretamente no Qwen local, sem serviços externos."""
    try:
        geracao = servico_llm.gerar(
            texto=requisicao.texto,
            operacao=requisicao.operacao,
            max_novos_tokens=requisicao.max_novos_tokens,
        )
    except TextoMuitoLongo as erro:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(erro)) from erro
    except TempoLimiteGeracao as erro:
        logger.warning("Limite de geração atingido: %s", erro)
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                            detail=str(erro)) from erro
    except MemoriaInsuficiente as erro:
        logger.warning("Memória CUDA insuficiente: %s", erro)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=str(erro)) from erro
    except ModeloIndisponivel as erro:
        logger.warning("LLM local indisponível: %s", erro)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=str(erro)) from erro
    except ModeloOcupado as erro:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(erro), headers={"Retry-After": "5"}) from erro
    except Exception:
        logger.exception("Falha inesperada na inferência local")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Falha interna ao processar o texto pelo modelo local.")
    return RespostaTexto(
        operacao=requisicao.operacao,
        texto_original=requisicao.texto,
        resultado=geracao.texto,
        modelo=MODEL_ID,
        execucao_local=True,
        tokens_entrada=geracao.tokens_entrada,
        tokens_saida=geracao.tokens_saida,
        tempo_processamento_ms=geracao.tempo_ms,
        aviso="Resultado gerado por IA local; verifique as informações antes de utilizá-las.",
    )
