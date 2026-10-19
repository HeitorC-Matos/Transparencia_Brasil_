from pathlib import Path
import pytest


@pytest.fixture
def dados_isolados(tmp_path, monkeypatch):
    """Cópia real dos dois CSVs do TP2 em diretório temporário para não alterar a entrega."""
    origem = Path(__file__).resolve().parents[1] / "data"
    pasta = tmp_path / "data"
    pasta.mkdir()
    for nome in ("amostra_dados.csv", "conteudo_web.csv"):
        (pasta / nome).write_bytes((origem / nome).read_bytes())
    monkeypatch.setenv("TP3_DATA_DIR", str(pasta))
    return pasta
