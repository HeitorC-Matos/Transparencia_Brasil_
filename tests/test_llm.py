"""Testes da preparação para LLMs com volume de dados variável.

Não exigem uma contagem fixa de fontes: coletas adicionais do Beautiful Soup
ou do Selenium podem aumentar o número de documentos e fragmentos.
"""
import json

from preparar_llm import fragmentar, preparar
from utils.dados import ler_amostra, ler_web


def total_esperado_web():
    return sum(
        len(list(fragmentar(f"{linha['titulo']}. {linha['texto']}".strip())))
        for _, linha in ler_web().iterrows()
    )


def test_fragmentacao_curta():
    assert list(fragmentar("pequeno texto")) == ["pequeno texto"]


def test_documentos_e_metadados(dados_isolados, tmp_path):
    relatorio = preparar(tmp_path / "jsonl")
    linhas = (tmp_path / "jsonl" / "documentos.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    documentos = [json.loads(linha) for linha in linhas]

    assert relatorio["total_web"] == total_esperado_web()
    assert relatorio["total_amostra_academica"] == len(ler_amostra())
    assert relatorio["quantidade_fragmentos"] == len(documentos)
    assert relatorio["quantidade_fragmentos"] == (
        relatorio["total_web"] + relatorio["total_amostra_academica"]
    )
    assert relatorio["cadastros_manuais_incluidos"] is False
    assert all("conteudo" in doc and "metadados" in doc for doc in documentos)
    assert len({doc["id"] for doc in documentos}) == len(documentos)
    fiscais = [doc for doc in documentos if doc["tipo"] == "despesa_academica"]
    assert len(fiscais) == len(ler_amostra())
    assert all(doc["metadados"]["verificado_em_fonte_oficial"] is False for doc in fiscais)


def test_preparacao_incorpora_coleta_selenium_sem_numero_fixo(dados_isolados, tmp_path):
    """Uma coleta adicional e um texto longo não devem invalidar o teste."""
    from coleta_selenium import URL_DINAMICA, salvar_registro

    salvar_registro({
        "titulo": "Transparência ativa via Selenium",
        "url": URL_DINAMICA,
        "texto": ("Informações públicas e controle social. " * 35).strip(),
        "metodo": "selenium+chromium",
        "data_coleta": "2026-10-19T18:00:00Z",
    }, pasta=dados_isolados)

    relatorio = preparar(tmp_path / "jsonl_com_selenium")
    assert relatorio["total_web"] == total_esperado_web()
    assert relatorio["total_web"] > len(ler_web())  # texto longo virou mais de 1 trecho
    assert relatorio["quantidade_fragmentos"] == (
        relatorio["total_web"] + relatorio["total_amostra_academica"]
    )
