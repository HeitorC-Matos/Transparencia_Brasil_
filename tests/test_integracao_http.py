"""Contratos do cliente HTTP utilizado diretamente pelas páginas Streamlit."""
from fastapi.testclient import TestClient

from api.main import app
from utils.api_client import (
    APIIndisponivel, cadastrar_despesa, consultar_conteudo_web,
    consultar_despesas, consultar_estatisticas, verificar_api,
)


def test_cliente_http_consulta_api_real_em_memoria(dados_isolados):
    sessao = TestClient(app)
    assert verificar_api(sessao=sessao)
    sp = consultar_despesas(sigla="SP", ano=2025, origem="amostra_academica", sessao=sessao)
    assert len(sp) == 3
    assert set(sp["origem"]) == {"amostra_academica"}
    assert consultar_estatisticas(sessao=sessao)["quantidade"] == 9
    assert len(consultar_conteudo_web(sessao=sessao)) == 3


def test_cliente_post_via_api_preserva_amostra(dados_isolados):
    sessao = TestClient(app)
    original = (dados_isolados / "amostra_dados.csv").read_bytes()
    cadastrado = cadastrar_despesa({
        "sigla": "BA", "ano": 2025, "funcao": "Saúde",
        "valor_despesa": 2_000, "populacao": 15000000,
    }, sessao=sessao)
    assert cadastrado["origem"] == "manual"
    assert len(consultar_despesas(origem="manual", sessao=sessao)) == 1
    assert (dados_isolados / "amostra_dados.csv").read_bytes() == original


def test_cliente_http_sem_api_retorna_falha_legivel():
    class SemConexao:
        def get(self, url, params=None, timeout=None):
            import requests
            raise requests.ConnectionError("servidor desligado")

    assert not verificar_api(sessao=SemConexao())
    try:
        consultar_despesas(sessao=SemConexao())
    except APIIndisponivel as erro:
        assert "/despesas" in str(erro)
    else:
        raise AssertionError("O cliente deveria informar APIIndisponivel")


def test_pagina_streamlit_tem_fluxo_get_post():
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "pages" / "5_API_FastAPI.py").read_text(encoding="utf-8")
    assert "consultar_despesas(" in codigo
    assert "cadastrar_despesa(" in codigo
    assert "st.form(" in codigo
    assert "ler_manuais(" not in codigo


def test_api_expoe_coleta_selenium_quando_existe(dados_isolados):
    """Com arquivo produzido pelo Selenium, o GET incorpora a nova fonte."""
    from coleta_selenium import salvar_registro, URL_DINAMICA
    salvar_registro({
        "titulo": "Transparência ativa via navegador",
        "url": URL_DINAMICA,
        "texto": "Documento institucional obtido após renderização pelo navegador.",
        "metodo": "selenium+chromium", "data_coleta": "2026-10-19T18:00:00Z",
    }, dados_isolados)
    sessao = TestClient(app)
    conteudos = consultar_conteudo_web(sessao=sessao)
    assert len(conteudos) == 4
    assert "selenium+chromium" in set(conteudos["metodo"])
