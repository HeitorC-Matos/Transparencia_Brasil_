"""Executar na raiz do projeto:

python scripts/coletar_siconfi.py --ufs SP GO BA
python scripts/coletar_siconfi.py --todas
python scripts/coletar_siconfi.py --todas --somente-cache

O segundo comando reutiliza as consultas já feitas para SP/GO/BA e busca as demais.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.siconfi import UF_ORDENADAS, coletar


def main() -> int:
    parser = argparse.ArgumentParser(description="Coleta auditável de despesas declaradas ao Siconfi")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--ufs", nargs="+", default=["SP", "GO", "BA"],
                       help="Siglas para validar em escala reduzida (padrão: SP GO BA)")
    grupo.add_argument("--todas", action="store_true", help="Coletar 27 unidades da Federação")
    parser.add_argument("--anos", nargs="+", type=int, default=list(range(2021, 2026)),
                        help="Exercícios, por padrão 2021 2022 2023 2024 2025")
    parser.add_argument("--atualizar", action="store_true", help="Refazer consultas à API, ignorando cache")
    parser.add_argument("--somente-cache", action="store_true", help="Revalidar dados já baixados, sem rede")
    args = parser.parse_args()
    ufs = list(UF_ORDENADAS) if args.todas else [x.upper() for x in args.ufs]
    try:
        resultado = coletar(ufs, args.anos, usar_cache=not args.atualizar,
                           somente_cache=args.somente_cache)
    except (ValueError, OSError) as exc:
        print("Falha na execução:", exc, file=sys.stderr)
        return 1
    print(json.dumps(resultado.__dict__, ensure_ascii=False, indent=2))
    if resultado.situacao == "completo":
        print("Coleta completa: todos os conjuntos UF/ano possuem três funções validadas.")
        return 0
    print("ATENÇÃO: cobertura incompleta. Consulte pendências no manifesto; não trate como base nacional completa.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
