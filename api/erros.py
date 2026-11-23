"""Respostas de erro HTTP padronizadas, sem expor detalhes internos."""
from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DetalheCampo(BaseModel):
    campo: str
    tipo: str
    mensagem: str


class ErroPadronizado(BaseModel):
    codigo: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)
    requisicao_id: str = Field(min_length=1)
    detalhes: list[DetalheCampo] | None = None


class RespostaErro(BaseModel):
    erro: ErroPadronizado
    # Campo de compatibilidade: consumidores HTTP legados usam `detail`.
    detail: str | list[dict] | None = None


MENSAGENS = {
    400: ("REQUISICAO_INVALIDA", "A solicitação não pôde ser interpretada."),
    404: ("NAO_ENCONTRADO", "O endereço solicitado não existe."),
    405: ("METODO_NAO_PERMITIDO", "Método HTTP não permitido para esta rota."),
    422: ("ENTRADA_INVALIDA", "Verifique os dados enviados e tente novamente."),
    429: ("MODELO_OCUPADO", "O assistente está atendendo outra solicitação. Tente novamente em alguns instantes."),
    500: ("ERRO_INTERNO", "Não foi possível concluir a operação devido a uma falha interna."),
    503: ("MODELO_INDISPONIVEL", "O serviço de IA local não está disponível no momento."),
    504: ("TEMPO_LIMITE", "O processamento excedeu o tempo permitido. Reduza o texto ou tente novamente."),
}


def _identificador(request: Request) -> str:
    # Atribuído pelo servidor, nunca pelo valor fornecido no cabeçalho do usuário.
    identificador = getattr(request.state, "requisicao_id", None)
    if identificador is None:
        identificador = uuid4().hex
        request.state.requisicao_id = identificador
    return identificador


def _erro(request: Request, status_code: int, *, detail=None, codigo=None,
          mensagem=None, detalhes=None, headers=None) -> JSONResponse:
    codigo_padrao, mensagem_padrao = MENSAGENS.get(status_code, (
        "ERRO_HTTP", "A solicitação não pôde ser concluída."))
    conteudo = RespostaErro(
        erro=ErroPadronizado(
            codigo=codigo or codigo_padrao,
            mensagem=mensagem or mensagem_padrao,
            requisicao_id=_identificador(request),
            detalhes=detalhes,
        ),
        detail=detail,
    ).model_dump(mode="json", exclude_none=True)
    cabecalhos = {"X-Request-ID": _identificador(request), **(headers or {})}
    return JSONResponse(status_code=status_code, content=conteudo, headers=cabecalhos)


def configurar_erros(app: FastAPI) -> None:
    @app.middleware("http")
    async def incluir_id_requisicao(request: Request, call_next):
        _identificador(request)
        response = await call_next(request)
        response.headers["X-Request-ID"] = _identificador(request)
        return response

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request: Request, exc: RequestValidationError):
        detalhes = []
        legados = []
        for erro in exc.errors():
            nome = ".".join(str(x) for x in erro.get("loc", ()) if x != "body") or "corpo"
            tipo = str(erro.get("type", "invalid"))
            mensagem = str(erro.get("msg", "Valor inválido"))
            detalhes.append(DetalheCampo(campo=nome, tipo=tipo, mensagem=mensagem))
            # Não incluir `input` nem contexto da exceção: podem conter dados sensíveis.
            legados.append({"loc": [str(x) for x in erro.get("loc", ())],
                            "type": tipo, "msg": mensagem})
        return _erro(request, 422, detail=legados, detalhes=detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def excecao_http(request: Request, exc: StarletteHTTPException):
        # Preserva o `detail` já documentado e distingue falha fiscal de falha do Qwen.
        if exc.status_code == 503 and request.url.path.startswith("/dados-oficiais"):
            return _erro(request, 503, detail=exc.detail, headers=exc.headers,
                         codigo="BASE_OFICIAL_INDISPONIVEL",
                         mensagem="A base oficial está indisponível ou ainda não foi coletada.")
        return _erro(request, exc.status_code, detail=exc.detail, headers=exc.headers)

    @app.exception_handler(ResponseValidationError)
    async def saida_invalida(request: Request, exc: ResponseValidationError):
        logger.error("Resposta fora do contrato: requisição=%s rota=%s tipos=%s",
                     _identificador(request), request.url.path,
                     [e.get("type") for e in exc.errors()])
        return _erro(request, 500, codigo="RESPOSTA_INVALIDA",
                     mensagem="O serviço produziu uma resposta fora do formato esperado.")

    @app.exception_handler(Exception)
    async def falha_interna(request: Request, exc: Exception):
        logger.exception("Falha não tratada: requisição=%s rota=%s",
                         _identificador(request), request.url.path)
        return _erro(request, 500)
