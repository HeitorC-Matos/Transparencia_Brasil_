"""Coleta em navegador com Selenium, aguardando o DOM renderizado.

Fonte: portal oficial da Lei de Acesso à Informação (LAI).
Executar: python coleta_selenium.py
Saída isolada: data/conteudo_selenium.csv e data/conteudo_selenium.txt.

O Selenium aqui demonstra a extração após renderização, mas não afirmamos
que esta página EXIGE Javascript: HTML estático seria suficiente nesse caso.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from coleta_web import COLUNAS, PASTA_DADOS, interpretar_html

URL_DINAMICA = (
    "https://www.gov.br/acessoainformacao/pt-br/assuntos/"
    "transparencia-ativa/informacoes-obrigatorias"
)


def criar_navegador():
    """Chromium/Chrome em modo headless via Selenium WebDriver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opcoes = Options()
    opcoes.add_argument("--headless=new")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    if os.getenv("TP3_CHROMIUM_BIN"):
        opcoes.binary_location = os.environ["TP3_CHROMIUM_BIN"]
    caminho_driver = os.getenv("TP3_CHROMEDRIVER_PATH")
    if caminho_driver:
        return webdriver.Chrome(service=Service(caminho_driver), options=opcoes)
    return webdriver.Chrome(options=opcoes)  # Selenium Manager (driver compatível)


def extrair_renderizada(url: str = URL_DINAMICA, *, driver=None, esperar=None) -> dict:
    """Solicita uma URL real, espera texto presente no DOM e extrai conteúdo.

    `driver` e `esperar` são injetáveis nos testes; execução normal usa Selenium.
    """
    proprio = driver is None
    if proprio:
        driver = criar_navegador()
    try:
        driver.get(url)
        if esperar is None:
            from selenium.webdriver.support.ui import WebDriverWait
            esperar = lambda d: WebDriverWait(d, 25).until(  # noqa: E731
                lambda navegador: bool(
                    navegador.execute_script(
                        "return [...document.querySelectorAll('main p, article p, p')]"
                        ".some(e => e.innerText.trim().length >= 25)"
                    )
                )
            )
        esperar(driver)
        registro = interpretar_html(driver.page_source, url)
        registro["metodo"] = "selenium+chromium"
        return registro
    finally:
        if proprio:
            driver.quit()


def salvar_registro(registro: dict, pasta: Path = PASTA_DADOS) -> tuple[Path, Path]:
    """Só cria arquivos quando o navegador realmente extraiu texto válido."""
    pasta.mkdir(parents=True, exist_ok=True)
    csv = pasta / "conteudo_selenium.csv"
    txt = pasta / "conteudo_selenium.txt"
    pd.DataFrame([{campo: registro.get(campo, "") for campo in COLUNAS}], columns=COLUNAS).to_csv(
        csv, index=False, encoding="utf-8-sig"
    )
    txt.write_text(
        f"{registro['titulo']}\n{registro['url']}\n{registro['texto']}\n", encoding="utf-8"
    )
    return csv, txt


def main():
    try:
        registro = extrair_renderizada()
        csv, txt = salvar_registro(registro)
        print(f"Coleta Selenium executada em {registro['data_coleta']}: {registro['url']}")
        print(f"Arquivos gerados: {csv} e {txt}")
    except Exception as erro:
        # Não produz CSV fictício quando navegador, driver ou Internet falharem.
        print(f"Selenium não conseguiu coletar a página: {type(erro).__name__}: {erro}")
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
