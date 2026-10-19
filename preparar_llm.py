"""Gera documentos JSONL pequenos e rastreáveis para uma futura solução RAG.

Não faz chamadas a LLMs nem substitui o dataset original.
Execute: python preparar_llm.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from utils.dados import ler_amostra, ler_web, pasta_dados


def fragmentar(texto: str, max_caracteres: int = 1000, sobreposicao: int = 120):
    if not 0 <= sobreposicao < max_caracteres:
        raise ValueError("Sobreposição deve ser menor que o tamanho do fragmento")
    texto = " ".join(str(texto).split())
    passo = max_caracteres - sobreposicao
    for inicio in range(0, len(texto), passo):
        trecho = texto[inicio:inicio + max_caracteres]
        if trecho:
            yield trecho
        if inicio + max_caracteres >= len(texto):
            break


def documento(tipo: str, conteudo: str, origem: str, metadados: dict) -> list[dict]:
    docs = []
    hash_base = hashlib.sha256(f"{tipo}|{origem}|{conteudo}".encode("utf-8")).hexdigest()[:16]
    for n, trecho in enumerate(fragmentar(conteudo), start=1):
        docs.append({
            "id": f"{hash_base}-{n:03d}",
            "tipo": tipo,
            "origem": origem,
            "conteudo": trecho,
            "metadados": metadados,
        })
    return docs


def preparar(destino: Path | None = None) -> dict:
    destino = destino or (pasta_dados() / "llm")
    destino.mkdir(parents=True, exist_ok=True)
    documentos = []
    for _, registro in ler_web().iterrows():
        texto = f"{registro['titulo']}. {registro['texto']}".strip()
        documentos.extend(documento(
            "conteudo_web", texto, "coleta_web",
            {"titulo": registro["titulo"], "url": registro["url"],
             "metodo": str(registro.get("metodo", "coleta_historica_tp2")),
             "data_coleta": str(registro.get("data_coleta", "")),
             "nota": "Conteúdo coletado ou resumido conforme método indicado; conferir a fonte."},
        ))
    for _, linha in ler_amostra().iterrows():
        descricao = (
            f"Dado ilustrativo do projeto Transparência Brasil, ano {int(linha['ano'])}. "
            f"Estado: {linha['estado']} ({linha['sigla']}). "
            f"Função: {linha['funcao']}. "
            f"Valor da despesa no CSV acadêmico: R$ {float(linha['valor_despesa']):.2f}. "
            f"População de referência no CSV acadêmico: {int(linha['populacao'])}. "
            "Este valor não foi verificado automaticamente em dados oficiais."
        )
        documentos.extend(documento(
            "despesa_academica", descricao, "amostra_dados.csv",
            {"sigla": linha["sigla"], "ano": int(linha["ano"]),
             "funcao": linha["funcao"], "fonte_fiscal_indicada": linha["fonte_fiscal"],
             "fonte_populacao_indicada": linha["fonte_populacao"],
             "verificado_em_fonte_oficial": False},
        ))
    caminho = destino / "documentos.jsonl"
    with caminho.open("w", encoding="utf-8") as arq:
        for item in documentos:
            arq.write(json.dumps(item, ensure_ascii=False) + "\n")
    manifesto = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quantidade_fragmentos": len(documentos),
        "total_web": sum(item["tipo"] == "conteudo_web" for item in documentos),
        "total_amostra_academica": sum(item["tipo"] == "despesa_academica" for item in documentos),
        "cadastros_manuais_incluidos": False,
        "usa_modelo_llm": False,
        "observacao": "Dados da amostra do TP1/TP2 sem validação fiscal externa.",
    }
    (destino / "manifesto.json").write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifesto


if __name__ == "__main__":
    print(json.dumps(preparar(), ensure_ascii=False, indent=2))
