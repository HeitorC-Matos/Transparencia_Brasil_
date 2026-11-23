"""Teste HTTP REAL, sem simular a inferência. Exige API e Qwen já instalados.

Retorna código de saída 0 somente quando o endpoint gera resposta com o Qwen.
"""
from __future__ import annotations

import json
import os
import sys
from time import perf_counter

import requests

BASE = os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")
PAYLOAD = {
    "texto": (
        "O projeto Transparência Brasil apresenta uma amostra acadêmica de despesas "
        "de São Paulo, Goiás e Bahia. Os valores são ilustrativos e não constituem "
        "estatísticas fiscais oficiais nem registros auditados."
    ),
    "operacao": "resumo",
    "max_novos_tokens": 128,
}


def main() -> int:
    print("API:", BASE)
    try:
        saude = requests.get(BASE + "/ia/health", timeout=10)
        print("Estado do modelo:", saude.status_code, saude.text)
        inicio = perf_counter()
        resposta = requests.post(BASE + "/processar_texto", json=PAYLOAD, timeout=300)
        print("HTTP:", resposta.status_code)
        print("Tempo total da chamada (s):", round(perf_counter() - inicio, 2))
        print(json.dumps(resposta.json(), ensure_ascii=False, indent=2))
        if resposta.status_code != 200:
            return 1
        corpo = resposta.json()
        return 0 if (corpo.get("execucao_local") is True
                     and corpo.get("modelo") == "Qwen/Qwen3-4B-Instruct-2507"
                     and isinstance(corpo.get("resultado"), str)
                     and corpo["resultado"].strip()
                     and corpo.get("tokens_saida", 0) > 0) else 1
    except (requests.RequestException, ValueError) as erro:
        print("Falha na integração HTTP real:", erro)
        return 1


if __name__ == "__main__":
    sys.exit(main())
