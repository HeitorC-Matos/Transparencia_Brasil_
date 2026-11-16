"""Verifica a ordem do menu por inspeção estrutural, sem GPU ou navegador."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_menu_possui_ordem_solicitada_e_oculta_paginas_de_bastidores():
    arvore = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    navegacoes = [no for no in ast.walk(arvore)
                  if isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                  and no.func.attr == "navigation"]
    assert len(navegacoes) == 1
    paginas = navegacoes[0].args[0].elts
    titulos = []
    for pagina in paginas:
        assert isinstance(pagina, ast.Call) and pagina.func.attr == "Page"
        titulos.append(next(k.value.value for k in pagina.keywords if k.arg == "title"))
    assert titulos == ["App", "Gastos públicos", "Estatísticas", "Dados oficiais",
                       "Conteúdo da Web", "API FastAPI", "Assistente IA"]
    assert (ROOT / "pages/6_Preparacao_para_IA.py").is_file()
    assert (ROOT / "pages/3_Arquivos.py").is_file()
    assert "Preparação para IA" not in titulos
    assert "Arquivos" not in titulos
