"""Não duplicar o painel: a aba de gastos concentra análises e contexto de IA."""
from pathlib import Path
import ast

RAIZ = Path(__file__).resolve().parents[1]


def test_app_apenas_apresenta_e_dashboard_fica_nos_gastos():
    app = (RAIZ / "app.py").read_text(encoding="utf-8")
    pagina = (RAIZ / "pages/4_Estatisticas.py").read_text(encoding="utf-8")
    ui = (RAIZ / "utils/dashboard_ui.py").read_text(encoding="utf-8")
    assert 'st.title("📊 Transparência Brasil")' in app
    assert "exibir_dashboard()" not in app
    assert "st.bar_chart" not in app and "st.line_chart" not in app
    assert "exibir_dashboard()" in pagina
    assert "Gastos públicos" in pagina
    assert "Insights com Qwen" in ui
    assert "Análises detalhadas" in ui
    assert "exibir_analises_detalhadas(base, int(ano), ufs, funcoes)" in ui
    assert "sintetizar_dados_fiscais_ia(" in ui


def test_page_legada_fora_do_menu_mas_amostra_preservada():
    arvore = ast.parse((RAIZ / "app.py").read_text(encoding="utf-8"))
    menu = next(n for n in ast.walk(arvore) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "navigation")
    textos = [pagina.args[0].value for pagina in menu.args[0].elts[1:]]
    assert "pages/1_Gastos_publicos.py" not in textos
    assert "pages/4_Estatisticas.py" in textos
    assert (RAIZ / "data/amostra_dados.csv").exists()
    assert (RAIZ / "utils/estatisticas_amostra.py").exists()


def test_fontes_e_calculos_reutilizados_sem_duplicar_coleta():
    mod = (RAIZ / "utils/estatisticas_ui.py").read_text(encoding="utf-8")
    assert "consultar_dados_oficiais" not in mod
    assert "agregar_ufs(base," in mod
    assert "composicao(base," in mod
    assert "historico(base," in mod
    assert "montar_visao(base," in (RAIZ / "utils/dashboard_ui.py").read_text(encoding="utf-8")
