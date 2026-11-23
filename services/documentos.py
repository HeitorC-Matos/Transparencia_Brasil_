"""Catálogo de documentos coletados: somente arquivos locais conhecidos.

Não admite caminhos de arquivos informados pelo usuário nem consulta páginas externas.
As páginas podem ter mudado após a coleta; a data e a URL são preservadas.
"""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FONTES = (
    ("beautifulsoup", RAIZ / "data" / "conteudo_web.csv"),
    ("selenium", RAIZ / "data" / "conteudo_selenium.csv"),
)


class DocumentoNaoEncontrado(LookupError):
    pass


class CatalogoIndisponivel(ValueError):
    pass


@dataclass(frozen=True)
class Documento:
    id: str
    titulo: str
    url: str
    texto: str
    data_coleta: str
    metodo: str
    origem: str

    def metadados(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "url": self.url,
            "data_coleta": self.data_coleta,
            "metodo": self.metodo,
            "origem": self.origem,
            "caracteres": len(self.texto),
        }


def listar_documentos() -> list[Documento]:
    saida: dict[str, Documento] = {}
    for origem, caminho in FONTES:
        if not caminho.exists():
            continue
        try:
            with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
                leitor = csv.DictReader(arquivo)
                exigidas = {"titulo", "url", "texto", "data_coleta", "metodo"}
                if not leitor.fieldnames or not exigidas.issubset(leitor.fieldnames):
                    raise CatalogoIndisponivel(f"Campos obrigatórios ausentes no catálogo {origem}.")
                for linha in leitor:
                    titulo = (linha.get("titulo") or "").strip()
                    url = (linha.get("url") or "").strip()
                    texto = (linha.get("texto") or "").strip()
                    if not titulo or not url or not texto or not url.startswith(("https://", "http://")):
                        continue
                    identidade = hashlib.sha256(f"{origem}|{url}|{titulo}".encode("utf-8")).hexdigest()[:20]
                    documento = Documento(
                        id=f"doc-{identidade}", titulo=titulo, url=url, texto=texto,
                        data_coleta=(linha.get("data_coleta") or "").strip(),
                        metodo=(linha.get("metodo") or origem).strip(), origem=origem,
                    )
                    saida[documento.id] = documento
        except (OSError, UnicodeError, csv.Error) as exc:
            raise CatalogoIndisponivel(f"Não foi possível ler o catálogo {origem}.") from exc
    return sorted(saida.values(), key=lambda d: (d.origem, d.titulo.casefold()))


def obter_documento(documento_id: str) -> Documento:
    for documento in listar_documentos():
        if documento.id == documento_id:
            return documento
    raise DocumentoNaoEncontrado("Documento não encontrado no catálogo local.")
