"""Verificação não destrutiva das fontes do dashboard pelo HTTP da FastAPI.

Uso (FastAPI ligada): python scripts/verificar_dashboard.py
Não carrega o Qwen, não edita dados e não executa scraping.
"""
from __future__ import annotations

import os
import sys

import requests


BASE = os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")


def conferir():
    with requests.Session() as cliente:
        saude = cliente.get(f"{BASE}/health", timeout=15)
        saude.raise_for_status()
        assert saude.json().get("status") == "ok", "FastAPI não retornou status ok"

        status_r = cliente.get(f"{BASE}/dados-oficiais/status", timeout=20)
        status_r.raise_for_status()
        status = status_r.json()
        print("Coleta:", status.get("situacao"), "| Registros:", status.get("registros_validados"))

        dados_r = cliente.get(f"{BASE}/dados-oficiais", params={"ano": 2025, "limite": 1000}, timeout=20)
        dados_r.raise_for_status()
        objeto = dados_r.json()
        dados = objeto.get("dados")
        assert isinstance(dados, list), "Formato de dados oficiais inesperado"
        assert len(dados) == objeto.get("total"), "Consulta paginada incompleta"
        assert all(l.get("ano") == 2025 and l.get("fonte_url") for l in dados), "Ano ou fonte inválida"
        print("Registros oficiais em 2025:", len(dados), "| UFs:", len({r["uf"] for r in dados}))

        docs_r = cliente.get(f"{BASE}/ia/documentos", timeout=20)
        docs_r.raise_for_status()
        catalogo = docs_r.json()
        assert isinstance(catalogo, list), "Catálogo de documentos inválido"
        print("Documentos institucionais no catálogo:", len(catalogo))

        ia_r = cliente.get(f"{BASE}/ia/health", timeout=20)
        ia_r.raise_for_status()
        print("Estado do Qwen (sem carregá-lo):", ia_r.json().get("status"))
        print("OK: as fontes do dashboard respondem por HTTP. Teste a interface no Streamlit separadamente.")


if __name__ == "__main__":
    try:
        conferir()
    except (requests.RequestException, ValueError, AssertionError, KeyError, TypeError) as exc:
        print("FALHA:", exc, file=sys.stderr)
        raise SystemExit(1)
