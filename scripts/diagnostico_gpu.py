"""Diagnóstico sem download de pesos e sem carregar o LLM."""
from __future__ import annotations

from importlib import metadata
from pathlib import Path
import sys

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz))
from services.llm_service import ServicoLLM  # noqa: E402


def main() -> None:
    print("Python:", sys.version.split()[0])
    for nome in ("torch", "transformers", "accelerate", "bitsandbytes", "huggingface-hub"):
        try:
            print(f"{nome}: {metadata.version(nome)}")
        except metadata.PackageNotFoundError:
            print(f"{nome}: NÃO INSTALADO")
    try:
        import torch
        print("CUDA disponível:", torch.cuda.is_available())
        print("Versão CUDA utilizada pelo PyTorch:", torch.version.cuda)
        if torch.cuda.is_available():
            for idx in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(idx)
                print(f"GPU {idx}: {props.name}, VRAM: {props.total_memory / (1024**3):.2f} GiB")
    except ImportError:
        print("PyTorch não instalado.")
    print("Estado dos arquivos do modelo:", ServicoLLM().status())


if __name__ == "__main__":
    main()
