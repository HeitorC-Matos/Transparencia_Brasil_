"""Teste real da nova sumarização na GPU, via FastAPI, sem modificar arquivos."""
from __future__ import annotations

import argparse
import sys

import requests


def testar(base: str, fiscal: bool):
    raiz = base.rstrip("/")
    status = requests.get(raiz + "/ia/health", timeout=15)
    status.raise_for_status()
    print("Modelo:", status.json()["status"])
    documentos = requests.get(raiz + "/ia/documentos", timeout=15)
    documentos.raise_for_status()
    fontes = documentos.json()
    if not fontes:
        raise RuntimeError("Não há documentos institucionais disponíveis.")
    primeiro = min(fontes, key=lambda d: d["caracteres"])
    corpo = {"documento_id": primeiro["id"], "modo": "executivo",
             "versao_prompt": "fundamentado", "max_novos_tokens": 128}
    print("Resumindo:", primeiro["titulo"])
    resposta = requests.post(raiz + "/ia/resumir_documento", json=corpo, timeout=300)
    resposta.raise_for_status()
    dados = resposta.json()
    assert dados["execucao_local"] is True and dados["resultado"].strip()
    assert primeiro["url"] in dados["fontes"]
    print("RESUMO DOCUMENTAL:", dados["resultado"])
    print("Tokens:", dados["tokens_entrada"], "/", dados["tokens_saida"])
    if fiscal:
        print("Gerando síntese fiscal...")
        resposta_f = requests.post(raiz + "/ia/sintese_fiscal", json={
            "ufs": ["SP", "GO", "BA"], "ano": 2025,
            "funcoes": ["Saúde", "Educação", "Segurança Pública"],
            "modo": "executivo", "versao_prompt": "fundamentado",
            "max_novos_tokens": 128,
        }, timeout=300)
        resposta_f.raise_for_status()
        fiscal_json = resposta_f.json()
        assert fiscal_json["execucao_local"] is True and fiscal_json["resultado"].strip()
        assert fiscal_json["metadados"]["registros"] == 9
        print("SÍNTESE FISCAL:", fiscal_json["resultado"])
    print("Teste HTTP com inferência real concluído.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valida sumarização real pelo Qwen local.")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--fiscal", action="store_true", help="Executa também a síntese fiscal.")
    args = parser.parse_args()
    try:
        testar(args.api, args.fiscal)
    except (requests.RequestException, RuntimeError, AssertionError) as erro:
        print(f"Falha no teste real: {erro}", file=sys.stderr)
        sys.exit(1)
