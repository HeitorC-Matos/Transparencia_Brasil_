"""Experimento real e reproduzível dos três prompts por HTTP local.

Executar com FastAPI e Qwen na GPU. Não atribui notas de qualidade automaticamente:
as avaliações de fidelidade e clareza devem ser preenchidas por quem lê as fontes.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


def avaliar(base: str, destino: Path, documento_id: str | None):
    origem = base.rstrip("/")
    sessao = requests.Session()
    documentos = sessao.get(origem + "/ia/documentos", timeout=15)
    documentos.raise_for_status()
    catalogo = documentos.json()
    if not catalogo:
        raise RuntimeError("Nenhum documento coletado disponível para avaliação.")
    escolhido = next((d for d in catalogo if d["id"] == documento_id), None) if documento_id else catalogo[0]
    if escolhido is None:
        raise ValueError("Documento informado não consta no catálogo.")
    resultados = []
    for versao in ("basico", "estruturado", "fundamentado"):
        corpo = {
            "documento_id": escolhido["id"], "modo": "executivo",
            "versao_prompt": versao, "max_novos_tokens": 384,
        }
        print(f"Executando prompt {versao} com o Qwen local...")
        resposta = sessao.post(origem + "/ia/resumir_documento", json=corpo, timeout=300)
        resposta.raise_for_status()
        data = resposta.json()
        resultados.append({
            "versao_prompt": versao, "resultado": data["resultado"],
            "tokens_entrada": data["tokens_entrada"],
            "tokens_saida": data["tokens_saida"],
            "tempo_processamento_ms": data["tempo_processamento_ms"],
            "etapas_geracao": data["etapas_geracao"],
            "avaliacao_humana": {"fidelidade_fonte_0a5": None,
                                 "pontos_centrais_0a5": None,
                                 "clareza_0a5": None,
                                 "inclusoes_nao_fundamentadas": None,
                                 "comentarios": ""},
        })
    payload = {
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "modelo": data["modelo"], "modo": "executivo",
        "documento": escolhido,
        "metodologia": "Mesmo documento, parâmetros e modelo; comparar três versões de prompt.",
        "aviso": "Métricas de qualidade exigem revisão humana. Nenhuma nota foi presumida.",
        "resultados": resultados,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Experimento registrado em: {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparação experimental dos prompts de sumarização.")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--documento-id", default=None)
    parser.add_argument("--saida", type=Path, default=Path("resultados") / "avaliacao_prompts_local.json")
    args = parser.parse_args()
    avaliar(args.api, args.saida, args.documento_id)
