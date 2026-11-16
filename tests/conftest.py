from pathlib import Path
import pytest


@pytest.fixture
def dados_isolados(tmp_path, monkeypatch):
    """Cópia dos CSVs para diretório temporário sem modificar os originais."""
    origem = Path(__file__).resolve().parents[1] / "data"
    pasta = tmp_path / "data"
    pasta.mkdir()
    for nome in ("amostra_dados.csv", "conteudo_web.csv"):
        (pasta / nome).write_bytes((origem / nome).read_bytes())
    monkeypatch.setenv("TP3_DATA_DIR", str(pasta))
    return pasta
