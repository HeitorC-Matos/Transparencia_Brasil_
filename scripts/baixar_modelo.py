"""Baixa somente arquivos necessários do Qwen para a pasta ignorada pelo Git.

Executar UMA VEZ com internet; o FastAPI exige apenas arquivos locais.
"""
from __future__ import annotations

from pathlib import Path
import sys

PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJETO))
from services.llm_service import ServicoLLM, MODEL_ID  # noqa: E402


def main() -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as erro:
        raise SystemExit("Instale primeiro: python -m pip install -r requirements-llm.txt") from erro
    destino = ServicoLLM().caminho
    destino.mkdir(parents=True, exist_ok=True)
    print(f"Origem: {MODEL_ID}\nDestino: {destino}")
    print("Baixando pesos, configuração e tokenizador. Isso requer internet e espaço em disco.")
    caminho = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(destino),
        allow_patterns=["*.safetensors", "*.json", "*.model", "*.txt", "*.tiktoken", "*.jinja"],
    )
    arquivos_esperados = (
        (destino / "config.json").exists()
        and (destino / "tokenizer_config.json").exists()
        and bool(list(destino.glob("*.safetensors")))
    )
    if not arquivos_esperados:
        raise SystemExit("Download incompleto: configuração, tokenizador ou pesos não encontrados.")
    print(f"Download concluído e arquivos básicos conferidos em: {caminho}")
    print("A partir de agora a API pode carregar os arquivos sem conexão externa.")


if __name__ == "__main__":
    main()
