"""Diagnóstico HTTP do contrato de erros sem carregar o modelo Qwen."""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")


def consultar(metodo: str, rota: str, dados: dict | None = None):
    req = Request(
        URL + rota,
        data=json.dumps(dados).encode("utf-8") if dados is not None else None,
        method=metodo,
        headers={"Content-Type": "application/json"} if dados is not None else {},
    )
    try:
        with urlopen(req, timeout=10) as resposta:
            return resposta.status, resposta.headers, json.load(resposta)
    except HTTPError as erro:
        with erro:
            return erro.code, erro.headers, json.load(erro)


def main() -> int:
    casos = [
        ("GET", "/health", None, 200, None),
        ("GET", "/ia/health", None, 200, None),
        ("POST", "/processar_texto", {"texto": "  ", "operacao": "resumo"}, 422, "ENTRADA_INVALIDA"),
        ("GET", "/rota-inexistente-de-teste", None, 404, "NAO_ENCONTRADO"),
    ]
    try:
        for metodo, rota, corpo, esperado, codigo in casos:
            status, headers, resposta = consultar(metodo, rota, corpo)
            correto = status == esperado and bool(headers.get("X-Request-ID"))
            if codigo:
                correto = correto and resposta.get("erro", {}).get("codigo") == codigo
            situacao = "OK" if correto else "FALHOU"
            print(f"{situacao}: {metodo} {rota} -> HTTP {status}; ID {headers.get('X-Request-ID')}")
            if not correto:
                print("Resposta:", json.dumps(resposta, ensure_ascii=False, indent=2))
                return 1
    except (URLError, TimeoutError, ValueError) as erro:
        print("FALHOU: não foi possível consultar a API. Inicie o Uvicorn.")
        print(f"Detalhe técnico: {erro}")
        return 1
    print("Verificação HTTP concluída. O modelo não foi carregado neste teste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
