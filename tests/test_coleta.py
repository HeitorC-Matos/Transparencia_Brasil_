from pathlib import Path

import pandas as pd
import requests

from coleta_web import interpretar_html, atualizar_coleta


HTML = """<html><head><title>Teste</title></head>
<body><nav><p>texto de menu que não deve aparecer no conteúdo</p></nav>
<main><h1>ODS 16 - Transparência</h1>
<p>Instituições responsáveis facilitam o acesso às informações públicas.</p></main>
<script>var x = 4</script></body></html>"""


def test_extracao_html_remove_menu():
    conteudo = interpretar_html(HTML, "https://exemplo.org/transparencia")
    assert conteudo["titulo"] == "ODS 16 - Transparência"
    assert "Instituições responsáveis" in conteudo["texto"]
    assert "texto de menu" not in conteudo["texto"]
    assert conteudo["metodo"] == "requests+beautifulsoup"


class SessaoComErro:
    def get(self, url, timeout):
        raise requests.ConnectionError("sem conexão no teste")


def test_falha_preserva_dado_anterior(tmp_path):
    url = "https://exemplo.org/documento"
    pd.DataFrame([{"titulo": "Salvo", "url": url, "texto": "Texto anterior"}]).to_csv(
        tmp_path / "conteudo_web.csv", index=False, encoding="utf-8-sig"
    )
    sucesso, erros = atualizar_coleta(tmp_path, urls=[url], sessao=SessaoComErro())
    assert (sucesso, erros) == (0, 1)
    novo = pd.read_csv(tmp_path / "conteudo_web.csv")
    assert novo.iloc[0]["texto"] == "Texto anterior"
    assert (tmp_path / "conteudo_web.txt").exists()

class RespostaFake:
    text = HTML

    def raise_for_status(self):
        return None


class SessaoSucesso:
    def get(self, url, timeout):
        assert timeout == 20
        return RespostaFake()


def test_coleta_grava_csv_txt_com_metadados(tmp_path):
    url = "https://exemplo.org/ods16"
    sucesso, erros = atualizar_coleta(tmp_path, urls=[url], sessao=SessaoSucesso())
    assert (sucesso, erros) == (1, 0)
    csv = pd.read_csv(tmp_path / "conteudo_web.csv")
    assert list(csv.columns) == ["titulo", "url", "texto", "data_coleta", "metodo"]
    assert csv.iloc[0]["metodo"] == "requests+beautifulsoup"
    assert csv.iloc[0]["data_coleta"]
    assert "Instituições responsáveis" in (tmp_path / "conteudo_web.txt").read_text(encoding="utf-8")
