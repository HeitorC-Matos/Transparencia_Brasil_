"""Coleta via Requests + Beautiful Soup em fontes oficiais verificáveis.

Mantenha as duas URLs do TP2 e acrescente a página de transparência da CGU.
Para aquisição com navegador, veja coleta_selenium.py.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URLS = [
    "https://brasil.un.org/pt-br/sdgs/16",
    "https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos",
    "https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica",
]
PASTA_DADOS = Path(__file__).resolve().parent / "data"
COLUNAS = ["titulo", "url", "texto", "data_coleta", "metodo"]


def criar_sessao():
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": "TransparenciaBrasilTP3/1.0 (uso academico)"})
    politica = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    sessao.mount("https://", HTTPAdapter(max_retries=politica))
    return sessao


def interpretar_html(html: str, url: str) -> dict:
    """Extrai título e parágrafos reais, ignorando scripts, menus e rodapés."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Somente URLs HTTP(S) são aceitas")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script, style, nav, footer, header, noscript"):
        tag.decompose()
    titulo_tag = soup.find("h1") or soup.title
    titulo = titulo_tag.get_text(" ", strip=True) if titulo_tag else parsed.netloc
    titulo = re.sub(r"\s+", " ", titulo).strip()
    corpo = soup.find("main") or soup.find("article") or soup.body or soup
    partes = []
    vistos = set()
    for tag in corpo.find_all("p"):
        texto = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if len(texto) >= 25 and texto not in vistos:
            partes.append(texto)
            vistos.add(texto)
        if len(partes) == 15:
            break
    if not partes:
        raise ValueError("Página sem parágrafos úteis; talvez exija conteúdo dinâmico")
    return {
        "titulo": titulo, "url": url, "texto": " ".join(partes)[:12000],
        "data_coleta": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metodo": "requests+beautifulsoup",
    }


def extrair_pagina(url: str, sessao=None) -> dict:
    cliente = sessao or criar_sessao()
    resposta = cliente.get(url, timeout=20)
    resposta.raise_for_status()
    return interpretar_html(resposta.text, url)


def atualizar_coleta(pasta: Path = PASTA_DADOS, urls=None, sessao=None) -> tuple[int, int]:
    """Se uma fonte falhar, conserva sua última versão local, sem inventar atualizações."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_csv = pasta / "conteudo_web.csv"
    anteriores = {}
    if caminho_csv.exists():
        for registro in pd.read_csv(caminho_csv, encoding="utf-8-sig").fillna("").to_dict("records"):
            anteriores[str(registro["url"])] = registro
    fontes = urls if urls is not None else URLS
    coletados, erros = 0, 0
    cliente = sessao or criar_sessao()
    resultados = []
    for url in fontes:
        try:
            pagina = extrair_pagina(url, cliente)
            coletados += 1
            print(f"Coletada: {url}")
        except (requests.RequestException, ValueError) as erro:
            erros += 1
            if url not in anteriores:
                print(f"Falha sem versão local para {url}: {erro}")
                continue
            pagina = anteriores[url]
            pagina.setdefault("data_coleta", "")
            pagina.setdefault("metodo", "coleta_anterior")
            print(f"Falha em {url}; preservando versão anterior: {erro}")
        resultados.append({chave: pagina.get(chave, "") for chave in COLUNAS})
    if not resultados:
        print("Nenhum dado disponível. Arquivos existentes não foram sobrescritos.")
        return 0, erros
    tabela = pd.DataFrame(resultados, columns=COLUNAS)
    tabela.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    with (pasta / "conteudo_web.txt").open("w", encoding="utf-8") as arquivo:
        for pagina in resultados:
            arquivo.write(f"{pagina['titulo']}\n{pagina['url']}\n{pagina['texto']}\n\n")
    print(f"data/conteudo_web.csv e .txt atualizados ({coletados} sucesso(s), {erros} falha(s)).")
    return coletados, erros


def main():
    atualizar_coleta()


if __name__ == "__main__":
    main()
