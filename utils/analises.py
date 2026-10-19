"""Funções testáveis compartilhadas entre Streamlit e testes."""
from collections import Counter
import re

import pandas as pd

STOPWORDS = {
    "para", "como", "mais", "pela", "pelo", "com", "dos", "das", "uma",
    "que", "por", "nos", "nas", "aos", "seus", "suas", "sobre", "entre",
    "ser", "são", "também", "estão", "este", "esta", "pela", "pelo",
}


def formatar_reais(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def palavras_frequentes(textos, minimo: int = 4, quantidade: int = 15):
    texto = " ".join(str(item) for item in textos if item is not None)
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto.lower())
    return Counter(
        palavra for palavra in palavras
        if len(palavra) >= minimo and palavra not in STOPWORDS
    ).most_common(quantidade)


def gasto_por_habitante(df: pd.DataFrame) -> pd.DataFrame:
    """Valores por pessoa: soma apenas despesas (não soma populações repetidas)."""
    agrupado = df.groupby(["estado", "ano"], as_index=False).agg(
        total=("valor_despesa", "sum"),
        populacao=("populacao", "first"),
    )
    agrupado["valor_por_habitante"] = agrupado["total"] / agrupado["populacao"]
    return agrupado
