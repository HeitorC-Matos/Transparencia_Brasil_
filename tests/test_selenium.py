"""Testes sem rede para conferir chamada ao navegador e persistência.

Não se trata de uma navegação real no portal governamental (exige Internet/driver).
"""
import pandas as pd

from coleta_selenium import extrair_renderizada, salvar_registro, URL_DINAMICA


class NavegadorSimulado:
    def __init__(self):
        self.url = None
        self.page_source = """<html><body><main><h1>Informações obrigatórias</h1>
        <p>Órgãos públicos divulgam informações sobre despesas e receitas orçamentárias
        de modo a permitir o controle social dos recursos.</p></main></body></html>"""

    def get(self, url):
        self.url = url


def test_selenium_navega_extrai_html_renderizado_e_salva(tmp_path):
    navegador = NavegadorSimulado()
    aguardou = []
    def aguardar(driver):
        aguardou.append(driver)
    registro = extrair_renderizada(URL_DINAMICA, driver=navegador, esperar=aguardar)
    assert navegador.url == URL_DINAMICA
    assert aguardou == [navegador]
    assert registro["metodo"] == "selenium+chromium"
    assert "despesas e receitas" in registro["texto"]
    csv, txt = salvar_registro(registro, pasta=tmp_path)
    df = pd.read_csv(csv)
    assert len(df) == 1
    assert df.iloc[0]["metodo"] == "selenium+chromium"
    assert "controle social" in txt.read_text(encoding="utf-8")


def test_selenium_nao_fabrica_resultado_sem_texto():
    class SemConteudo(NavegadorSimulado):
        page_source = "<html><body><h1>Vazio</h1></body></html>"
        def __init__(self):
            super().__init__()
            self.page_source = "<html><body><h1>Vazio</h1></body></html>"
    try:
        extrair_renderizada(driver=SemConteudo(), esperar=lambda driver: None)
    except ValueError as erro:
        assert "sem parágrafos" in str(erro)
    else:
        raise AssertionError("Um documento vazio não pode virar dado coletado")
