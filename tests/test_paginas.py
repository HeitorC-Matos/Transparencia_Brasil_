import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_paginas_streamlit_organizadas():
    assert (ROOT / "app.py").exists()
    paginas = sorted((ROOT / "pages").glob("*.py"))
    assert len(paginas) >= 5
    for caminho in [ROOT / "app.py", ROOT / "api" / "main.py", *paginas]:
        ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
