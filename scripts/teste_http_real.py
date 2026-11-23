"""Smoke test repetível com Uvicorn + requests HTTP em localhost.

Uso: python -m scripts.teste_http_real
Sem tocar na amostra distribuída: todos os CSVs são copiados para /tmp.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from utils.api_client import cadastrar_despesa, consultar_despesas, verificar_api
from utils.dados import ROOT


def executar() -> None:
    with tempfile.TemporaryDirectory(prefix="tp3_http_") as temporario:
        for nome in ("amostra_dados.csv", "conteudo_web.csv"):
            shutil.copyfile(ROOT / "data" / nome, Path(temporario) / nome)
        with socket.socket() as tomada:
            tomada.bind(("127.0.0.1", 0))
            porta = tomada.getsockname()[1]
        url = f"http://127.0.0.1:{porta}"
        ambiente = os.environ.copy()
        ambiente["TP3_DATA_DIR"] = temporario
        ambiente["TP3_API_URL"] = url
        processo = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", str(porta)],
            cwd=ROOT, env=ambiente, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        anterior = os.environ.get("TP3_API_URL")
        os.environ["TP3_API_URL"] = url
        try:
            for _ in range(75):
                if processo.poll() is not None:
                    raise RuntimeError("O servidor Uvicorn encerrou antes da conexão")
                try:
                    if requests.get(url + "/health", timeout=0.7).status_code == 200:
                        break
                except requests.RequestException:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Não foi possível iniciar Uvicorn em localhost")
            assert verificar_api()
            assert len(consultar_despesas(sigla="SP")) == 3
            resposta = cadastrar_despesa({
                "sigla": "SP", "ano": 2025, "funcao": "Educação",
                "valor_despesa": 2345.0, "populacao": 46_000_000,
            })
            assert resposta["origem"] == "manual"
            assert len(consultar_despesas(origem="manual")) == 1
            assert len(consultar_despesas(origem="amostra_academica")) == 9
            assert (ROOT / "data" / "amostra_dados.csv").read_bytes() == (Path(temporario) / "amostra_dados.csv").read_bytes()
            print("OK: GET /health, GET /despesas, POST /despesas e GET de registro manual via HTTP localhost")
        finally:
            if anterior is None:
                os.environ.pop("TP3_API_URL", None)
            else:
                os.environ["TP3_API_URL"] = anterior
            processo.terminate()
            try:
                processo.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.communicate()


if __name__ == "__main__":
    executar()
