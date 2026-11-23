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
    """Erro de comunicação ou de API, com código e orientação para a interface."""

    def __init__(self, mensagem: str, *, status_code: int | None = None,
                 codigo: str | None = None, requisicao_id: str | None = None,
                 retry_after: str | None = None):
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.requisicao_id = requisicao_id
        self.retry_after = retry_after


def _interpretar_erro_http(erro: requests.HTTPError, metodo: str, caminho: str):
    resposta = erro.response
    status = getattr(resposta, "status_code", None)
    try:
        corpo = resposta.json()
    except (ValueError, AttributeError):
        corpo = {}
    corpo = corpo if isinstance(corpo, dict) else {}
    contrato = corpo.get("erro", {})
    contrato = contrato if isinstance(contrato, dict) else {}
    mensagens = {
        422: "Os dados informados não passaram na validação. Revise o texto e a operação.",
        429: "O assistente está processando outra solicitação. Aguarde e tente novamente.",
        503: "O modelo de IA não está disponível. Confira o diagnóstico do Qwen e os logs da API.",
        504: "O processamento ultrapassou o tempo permitido. Tente um texto menor.",
        500: "Ocorreu uma falha interna. Consulte os logs da FastAPI.",
    }
    mensagem = contrato.get("mensagem") if isinstance(contrato.get("mensagem"), str) else None
    if status == 503 and caminho.startswith("/dados-oficiais"):
        mensagem = "A base oficial do Siconfi não está disponível. Verifique a coleta local e o manifesto."
    elif status == 503 and caminho == "/ia/documentos":
        mensagem = "O catálogo de documentos coletados está indisponível. Confira os arquivos locais."
    elif status in mensagens:
        mensagem = mensagens[status]
    if not mensagem:
        mensagem = f"A API recusou a requisição ({status or 'erro HTTP'})."
    detalhe = corpo.get("detail")
    if status == 422 and caminho == "/ia/perguntar_dados" and isinstance(detalhe, str):
        mensagem = detalhe
    if status == 503 and caminho == "/ia/perguntar_dados" and isinstance(detalhe, str):
        mensagem = detalhe
    if status == 422 and isinstance(detalhe, list):
        campos = [str(i.get("loc", ["corpo"])[-1]) for i in detalhe[:3]
                  if isinstance(i, dict)]
        if campos:
            mensagem += " Campos: " + ", ".join(campos) + "."
    headers = getattr(resposta, "headers", {}) or {}
    return APIIndisponivel(
        mensagem, status_code=status, codigo=contrato.get("codigo"),
        requisicao_id=headers.get("X-Request-ID") or contrato.get("requisicao_id"),
        retry_after=headers.get("Retry-After"),
    )


def base_url() -> str:
    return os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")


def requisitar(metodo: str, caminho: str, *, parametros: dict | None = None,
               json: dict | None = None, sessao=None, timeout: int = 8) -> Any:
    """Faz a chamada HTTP; sessão injetável permite testes sem Internet."""
    cliente = sessao if sessao is not None else requests
    url = f"{base_url()}{caminho}"
    try:
        if metodo.upper() == "GET":
            resposta = cliente.get(url, params=parametros, timeout=timeout)
        elif metodo.upper() == "POST":
            resposta = cliente.post(url, json=json, timeout=timeout)
        else:
            raise ValueError("Método HTTP não suportado")
        resposta.raise_for_status()
        return resposta.json()
    except requests.HTTPError as erro:
        raise _interpretar_erro_http(erro, metodo, caminho) from erro
    except requests.Timeout as erro:
        raise APIIndisponivel(
            "Tempo de comunicação esgotado. Verifique se a FastAPI continua em execução.",
            codigo="TIMEOUT_COMUNICACAO",
        ) from erro
    except requests.ConnectionError as erro:
        raise APIIndisponivel(
            f"Não foi possível conectar à FastAPI local ({caminho}). Verifique se o servidor está ligado.",
            codigo="API_SEM_CONEXAO",
        ) from erro
    except (requests.RequestException, ValueError) as erro:
        raise APIIndisponivel(
            "A comunicação com a API falhou. Verifique os logs e a configuração do servidor.",
            codigo="FALHA_COMUNICACAO",
        ) from erro


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


def consultar_status_ia(*, sessao=None) -> dict:
    """Consulta o serviço de IA sem disparar o carregamento dos pesos."""
    resposta = requisitar("GET", "/ia/health", sessao=sessao)
    if not isinstance(resposta, dict) or "status" not in resposta:
        raise APIIndisponivel("Resposta de saúde do LLM fora do formato esperado")
    return resposta


def processar_texto_ia(texto: str, operacao: str = "resumo", *,
                       max_novos_tokens: int = 384, sessao=None) -> dict:
    """Faz inferência REAL pelo FastAPI; espera maior que rotas normais."""
    resposta = requisitar(
        "POST", "/processar_texto",
        json={"texto": texto, "operacao": operacao,
              "max_novos_tokens": max_novos_tokens},
        sessao=sessao, timeout=300,
    )
    if not isinstance(resposta, dict) or not isinstance(resposta.get("resultado"), str):
        raise APIIndisponivel("Resposta LLM fora do formato esperado")
    if resposta.get("execucao_local") is not True:
        raise APIIndisponivel("A API não confirmou execução local do modelo")
    return resposta


def consultar_status_dados_oficiais(*, sessao=None) -> dict:
    """Situação da carga oficial, sem usar dados ilustrativos como substitutos."""
    r = requisitar("GET", "/dados-oficiais/status", sessao=sessao)
    if not isinstance(r, dict) or "situacao" not in r:
        raise APIIndisponivel("Status da base Siconfi fora do contrato")
    return r


def consultar_dados_oficiais(*, uf: str | None = None, ano: int | None = None,
                             funcao: str | None = None, sessao=None) -> pd.DataFrame:
    """Consulta paginada aos registros declaratórios e validados do Siconfi."""
    filtros = {k: v for k, v in {"uf": uf, "ano": ano, "funcao": funcao}.items() if v is not None}
    linhas = []
    posicao = 0
    while True:
        resp = requisitar("GET", "/dados-oficiais", parametros={**filtros, "limite": 1000,
                                             "deslocamento": posicao}, sessao=sessao)
        if not isinstance(resp, dict) or not isinstance(resp.get("dados"), list):
            raise APIIndisponivel("Dados oficiais fora do contrato de resposta")
        lote = resp["dados"]
        linhas.extend(lote)
        posicao += len(lote)
        try:
            total = int(resp["total"])
        except (TypeError, KeyError, ValueError) as exc:
            raise APIIndisponivel("Total de dados oficiais inválido") from exc
        if posicao >= total:
            break
        if not lote:
            raise APIIndisponivel("Paginação oficial interrompida")
    df = pd.DataFrame(linhas)
    if not df.empty:
        for coluna in ("valor_reais", "ano", "periodo"):
            df[coluna] = pd.to_numeric(df[coluna], errors="raise")
    return df


def consultar_serie_oficial(uf: str, funcao: str, *, sessao=None) -> dict:
    r = requisitar("GET", "/dados-oficiais/serie",
                  parametros={"uf": uf, "funcao": funcao}, sessao=sessao)
    if not isinstance(r, dict) or not isinstance(r.get("dados"), list):
        raise APIIndisponivel("Série oficial fora do contrato")
    return r


def consultar_regioes_oficiais(ano: int, funcao: str, *, sessao=None) -> dict:
    r = requisitar("GET", "/dados-oficiais/regioes",
                  parametros={"ano": ano, "funcao": funcao}, sessao=sessao)
    if not isinstance(r, dict) or not isinstance(r.get("dados"), list):
        raise APIIndisponivel("Resposta de regiões fora do contrato")
    return r


def listar_documentos_ia(*, sessao=None) -> list[dict]:
    """Carrega o catálogo textual local via FastAPI, sem acessar os CSVs na página."""
    resultado = requisitar("GET", "/ia/documentos", sessao=sessao)
    if not isinstance(resultado, list) or any(
        not isinstance(doc, dict) or not isinstance(doc.get("id"), str)
        for doc in resultado
    ):
        raise APIIndisponivel("Catálogo de documentos fora do contrato esperado")
    return resultado


def resumir_documento_ia(documento_id: str, *, modo: str = "executivo",
                         versao_prompt: str = "fundamentado", max_novos_tokens: int = 384,
                         sessao=None) -> dict:
    resposta = requisitar(
        "POST", "/ia/resumir_documento",
        json={"documento_id": documento_id, "modo": modo,
              "versao_prompt": versao_prompt, "max_novos_tokens": max_novos_tokens},
        sessao=sessao, timeout=300,
    )
    if not isinstance(resposta, dict) or not isinstance(resposta.get("resultado"), str) \
            or resposta.get("execucao_local") is not True or not isinstance(resposta.get("fontes"), list):
        raise APIIndisponivel("Resposta documental fora do contrato esperado")
    return resposta


def sintetizar_dados_fiscais_ia(ufs: list[str], ano: int, funcoes: list[str], *,
                                modo: str = "executivo", versao_prompt: str = "fundamentado",
                                max_novos_tokens: int = 384, sessao=None) -> dict:
    resposta = requisitar(
        "POST", "/ia/sintese_fiscal",
        json={"ufs": ufs, "ano": ano, "funcoes": funcoes, "modo": modo,
              "versao_prompt": versao_prompt, "max_novos_tokens": max_novos_tokens},
        sessao=sessao, timeout=300,
    )
    if not isinstance(resposta, dict) or not isinstance(resposta.get("resultado"), str) \
            or resposta.get("execucao_local") is not True or not isinstance(resposta.get("fontes"), list):
        raise APIIndisponivel("Síntese fiscal fora do contrato esperado")
    return resposta


def perguntar_dados_ia(pergunta: str, ano_referencia: int = 2025, *,
                      usar_qwen: bool = True, max_novos_tokens: int = 384,
                      sessao=None) -> dict:
    """Responde com cálculos do Python; Qwen apenas complementa, quando solicitado."""
    resposta = requisitar(
        "POST", "/ia/perguntar_dados",
        json={"pergunta": pergunta, "ano_referencia": ano_referencia,
              "usar_qwen": usar_qwen, "max_novos_tokens": max_novos_tokens},
        sessao=sessao, timeout=300 if usar_qwen else 15,
    )
    if (not isinstance(resposta, dict) or not isinstance(resposta.get("resposta_calculada"), str)
            or not isinstance(resposta.get("dados"), list)
            or not isinstance(resposta.get("fontes"), list)
            or not isinstance(resposta.get("qwen_executado"), bool)):
        raise APIIndisponivel("Consulta fiscal fora do contrato esperado")
    return resposta
