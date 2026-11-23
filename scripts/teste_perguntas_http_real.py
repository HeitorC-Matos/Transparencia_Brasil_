"""Teste da consulta fiscal via HTTP, com complemento Qwen opcional.

Execute com FastAPI já iniciada:
  python scripts/teste_perguntas_http_real.py
  python scripts/teste_perguntas_http_real.py --com-qwen
"""
from __future__ import annotations

import argparse
import os
import sys

import requests

QUESTOES = (
    ("ranking", "Qual foi o estado que mais investiu na educação?"),
    ("consulta", "Quanto Goiás gastou com Saúde em 2024?"),
    ("comparacao", "Compare SP e BA na Segurança Pública em 2025."),
    ("evolucao", "Como evoluiu a Educação no DF de 2021 a 2025?"),
    ("participacao", "Qual a participação da Saúde nas três funções em Minas Gerais em 2025?"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida perguntas fiscais na FastAPI local.")
    parser.add_argument("--com-qwen", action="store_true", help="Também executa uma inferência na GPU")
    args = parser.parse_args()
    raiz = os.getenv("TP3_API_URL", "http://127.0.0.1:8000").rstrip("/")
    sessao = requests.Session()
    for i, (tipo, pergunta) in enumerate(QUESTOES):
        usar_qwen = bool(args.com_qwen and i == 0)
        try:
            resposta = sessao.post(
                raiz + "/ia/perguntar_dados",
                json={"pergunta": pergunta, "ano_referencia": 2025, "usar_qwen": usar_qwen,
                      "max_novos_tokens": 192},
                timeout=300 if usar_qwen else 20,
            )
            resposta.raise_for_status()
            dado = resposta.json()
            if dado.get("tipo") != tipo or not dado.get("dados") or not dado.get("fontes"):
                raise ValueError("Resposta sem tipo, registros ou fontes esperadas")
            if usar_qwen and not dado.get("qwen_executado"):
                raise ValueError("Resposta calculada, porém Qwen não executou: " + str(dado.get("aviso_ia")))
            print(f"OK {tipo}: {dado['resposta_calculada']}")
            if usar_qwen:
                print("QWEN EXECUTADO:", dado.get("explicacao_ia"))
        except (requests.RequestException, ValueError, KeyError) as erro:
            print(f"FALHA {tipo}: {erro}", file=sys.stderr)
            return 1
    print("VERIFICAÇÃO CONCLUÍDA: cinco intenções válidas; Qwen "
          + ("testado na primeira consulta." if args.com_qwen else "não carregado."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
