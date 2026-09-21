from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Páginas relacionadas ao tema do projeto e ao ODS 16.
URLS = [
    "https://brasil.un.org/pt-br/sdgs/16",
    "https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos",
]

PASTA_DADOS = Path(__file__).resolve().parent / "data"


def extrair_pagina(url):
    resposta = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resposta.raise_for_status()

    soup = BeautifulSoup(resposta.text, "html.parser")

    titulo = soup.find("h1")
    titulo = titulo.get_text(" ", strip=True) if titulo else soup.title.get_text(" ", strip=True)

    paragrafos = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
        if p.get_text(" ", strip=True)
    ]

    # Para o trabalho, basta uma quantidade limitada de texto da página.
    texto = " ".join(paragrafos[:8])

    return {
        "titulo": titulo,
        "url": url,
        "texto": texto,
    }


def main():
    registros = []

    for url in URLS:
        try:
            registros.append(extrair_pagina(url))
            print(f"Página coletada: {url}")
        except requests.RequestException as erro:
            print(f"Não foi possível coletar {url}: {erro}")

    if not registros:
        print("Nenhuma página foi coletada.")
        return

    PASTA_DADOS.mkdir(exist_ok=True)
    df = pd.DataFrame(registros)

    df.to_csv(
        PASTA_DADOS / "conteudo_web.csv",
        index=False,
        encoding="utf-8-sig",
    )

    with open(PASTA_DADOS / "conteudo_web.txt", "w", encoding="utf-8") as arquivo:
        for registro in registros:
            arquivo.write(registro["titulo"] + "\n")
            arquivo.write(registro["url"] + "\n")
            arquivo.write(registro["texto"] + "\n\n")

    print("Arquivos conteudo_web.csv e conteudo_web.txt foram salvos em data/.")


if __name__ == "__main__":
    main()
