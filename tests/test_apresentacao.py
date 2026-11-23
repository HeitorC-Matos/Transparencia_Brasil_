"""Garante nomenclatura de produto na interface, sem alterar os contratos HTTP."""
import re
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "app.py", *sorted((ROOT / "pages").glob("*.py")), ROOT / "utils" / "ui.py"]


def test_paginas_nao_exibem_rotulos_de_atividades():
    expressao = re.compile(r"\bTP\s*\d+\b|\bquest[aã]o\s*\d+\b|\brubrica\b", re.IGNORECASE)
    for caminho in PAGES:
        assert not expressao.search(caminho.read_text(encoding="utf-8")), str(caminho)


def test_pagina_principal_tem_titulo_e_recursos_neutros():
    texto = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'st.title("📊 Transparência Brasil")' in texto
    assert 'st.subheader("Recursos preservados")' in texto


def test_documentacao_openapi_sem_rotulo_de_atividade():
    dados = TestClient(app).get("/openapi.json").json()
    assert dados["info"]["title"] == "Transparência Brasil — API"
    assert "/processar_texto" in dados["paths"]


def test_pagina_assistente_nao_contem_rotulo_academico():
    texto = (ROOT / "pages" / "7_Assistente_IA.py").read_text(encoding="utf-8")
    assert "amostra ilustrativa" in texto
    assert "amostra acadêmica" not in texto
