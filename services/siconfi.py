"""Coleta verificável do RREO Anexo 02 (Siconfi/Tesouro Nacional).

O objetivo não é tratar todo registro retornado como despesa: selecionamos apenas
as três linhas sintéticas de função do quadro não intraorçamentário e a coluna
acumulada de despesas liquidadas no 6º bimestre. Respostas incompletas ou
ambíguas produzem pendências, nunca valores inventados.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from uuid import uuid4
import tempfile
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

import requests
from filelock import FileLock

from utils.dados import pasta_dados

API_BASE = "https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/rreo"
DOCUMENTACAO = "https://apidatalake.tesouro.gov.br/docs/siconfi/"
ANEXO = "RREO-Anexo 02"
PERIODO = 6
COLUNA = "DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)"
COD_CONTA = "RREO2TotalDespesas"  # quadro com exclusão de intraorçamentárias
FUNCOES_CODIGO = {"Educação": "12", "Saúde": "10", "Segurança Pública": "06"}
UF_IBGE = {
    "AC": (12, "Acre"), "AL": (27, "Alagoas"), "AP": (16, "Amapá"),
    "AM": (13, "Amazonas"), "BA": (29, "Bahia"), "CE": (23, "Ceará"),
    "DF": (53, "Distrito Federal"), "ES": (32, "Espírito Santo"),
    "GO": (52, "Goiás"), "MA": (21, "Maranhão"), "MT": (51, "Mato Grosso"),
    "MS": (50, "Mato Grosso do Sul"), "MG": (31, "Minas Gerais"),
    "PA": (15, "Pará"), "PB": (25, "Paraíba"), "PR": (41, "Paraná"),
    "PE": (26, "Pernambuco"), "PI": (22, "Piauí"), "RJ": (33, "Rio de Janeiro"),
    "RN": (24, "Rio Grande do Norte"), "RS": (43, "Rio Grande do Sul"),
    "RO": (11, "Rondônia"), "RR": (14, "Roraima"), "SC": (42, "Santa Catarina"),
    "SP": (35, "São Paulo"), "SE": (28, "Sergipe"), "TO": (17, "Tocantins"),
}
REGIOES = {
    "Norte": ("AC", "AP", "AM", "PA", "RO", "RR", "TO"),
    "Nordeste": ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "Centro-Oeste": ("DF", "GO", "MT", "MS"),
    "Sudeste": ("ES", "MG", "RJ", "SP"),
    "Sul": ("PR", "RS", "SC"),
}
UF_ORDENADAS = tuple(sorted(UF_IBGE))
CAMPOS_EXPORTADOS = (
    "uf", "estado", "ano", "funcao", "codigo_funcao", "valor_reais",
    "estagio", "periodo", "anexo", "cod_conta", "abrangencia",
    "origem", "fonte_url", "data_coleta_utc", "hash_fonte_sha256",
)


class FalhaColeta(RuntimeError):
    """O Siconfi não respondeu de forma completa ou segura."""


class InconsistenciaFiscal(ValueError):
    """Um valor é inválido ou não tem correspondência contábil inequívoca."""


def _limpar(texto: object) -> str:
    s = unicodedata.normalize("NFKD", str(texto or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().casefold()


def _decimal(valor: object) -> Decimal:
    if isinstance(valor, bool) or valor is None:
        raise InconsistenciaFiscal("Valor fiscal ausente ou não numérico")
    s = str(valor).strip()
    if not s:
        raise InconsistenciaFiscal("Valor fiscal vazio")
    # JSON da API normalmente utiliza ponto decimal. Aceitamos também formato pt-BR.
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation as exc:
        raise InconsistenciaFiscal(f"Valor fiscal inválido: {valor!r}") from exc
    if not d.is_finite() or d < 0:
        raise InconsistenciaFiscal(f"Valor fiscal não finito ou negativo: {valor!r}")
    return d


def diretorio_siconfi() -> Path:
    return pasta_dados() / "siconfi"


def _gravar_atomico(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=".tmp_siconfi_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as arq:
            arq.write(conteudo)
            arq.flush()
            os.fsync(arq.fileno())
        os.replace(temporario, caminho)
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parametros(uf: str, ano: int) -> dict:
    return {
        "an_exercicio": ano, "nr_periodo": PERIODO,
        "co_tipo_demonstrativo": "RREO", "no_anexo": ANEXO,
        "id_ente": UF_IBGE[uf][0],
        # Não aplicar co_esfera: evita omissões em casos de esfera especial do DF.
    }


class ClienteSiconfi:
    """Cliente HTTP com paginação, intervalos e repetição de falhas transitórias."""

    def __init__(self, sessao=None, intervalo: float = 1.1, dormir=time.sleep, relogio=time.monotonic):
        self.sessao = sessao or requests.Session()
        self.intervalo = intervalo
        self.dormir = dormir
        self.relogio = relogio
        self.ultima = None

    def _consultar(self, url: str, params: dict | None) -> dict:
        for tentativa in range(5):
            if self.ultima is not None:
                espera = self.intervalo - (self.relogio() - self.ultima)
                if espera > 0:
                    self.dormir(espera)
            self.ultima = self.relogio()
            try:
                resposta = self.sessao.get(
                    url, params=params, timeout=(15, 75),
                    headers={"Accept": "application/json", "User-Agent": "TransparenciaBrasil/1.0"},
                )
            except requests.RequestException as erro:
                if tentativa == 4:
                    raise FalhaColeta(f"Erro de rede ao acessar Siconfi: {type(erro).__name__}") from erro
                self.dormir(min(2 ** tentativa, 16))
                continue
            if resposta.status_code in (429, 500, 502, 503, 504):
                if tentativa == 4:
                    raise FalhaColeta(f"Siconfi indisponível: HTTP {resposta.status_code}")
                try:
                    pausa = max(float(resposta.headers.get("Retry-After", "0")), float(2 ** tentativa))
                except ValueError:
                    pausa = float(2 ** tentativa)
                self.dormir(min(pausa, 60))
                continue
            try:
                resposta.raise_for_status()
                payload = resposta.json()
            except (requests.RequestException, ValueError) as erro:
                raise FalhaColeta("Resposta HTTP/JSON inválida do Siconfi") from erro
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise FalhaColeta("Formato JSON inesperado: campo items ausente")
            return payload
        raise FalhaColeta("Limite de tentativas excedido")

    def buscar(self, uf: str, ano: int) -> tuple[list[dict], str]:
        if uf not in UF_IBGE or not 2021 <= ano <= 2025:
            raise ValueError("UF/ano fora do escopo da base histórica (2021–2025)")
        parametros = _parametros(uf, ano)
        url = API_BASE
        linhas: list[dict] = []
        vistos: set[str] = set()
        for _ in range(100):
            if url in vistos:
                raise FalhaColeta("Paginação circular detectada")
            vistos.add(url)
            payload = self._consultar(url, parametros)
            linhas.extend(payload["items"])
            proximo = None
            for link in payload.get("links", []):
                if isinstance(link, dict) and str(link.get("rel", "")).lower() == "next":
                    proximo = link.get("href")
                    break
            if not payload.get("hasMore", False):
                return linhas, requests.Request("GET", API_BASE, params=_parametros(uf, ano)).prepare().url
            if not proximo:
                raise FalhaColeta("Siconfi informou páginas adicionais, mas não forneceu link next")
            parsed = urlparse(proximo)
            if parsed.scheme != "https" or parsed.hostname != "apidatalake.tesouro.gov.br" or not parsed.path.endswith("/siconfi/tt/rreo"):
                raise FalhaColeta("Link de paginação inseguro ou inesperado")
            url, parametros = proximo, None
        raise FalhaColeta("Excedido o limite de 100 páginas do demonstrativo")


def normalizar(uf: str, ano: int, linhas: list[dict], url: str, coletado_em: str | None = None) -> list[dict]:
    """Retorna exatamente 3 funções ou gera pendência; nunca faz soma de linhas."""
    if uf not in UF_IBGE:
        raise ValueError("UF não reconhecida")
    if not isinstance(linhas, list):
        raise InconsistenciaFiscal("Resposta não contém lista de registros")
    encontrados: dict[str, list[dict]] = {f: [] for f in FUNCOES_CODIGO}
    totais_nao_intra: list[dict] = []
    for linha in linhas:
        if not isinstance(linha, dict):
            raise InconsistenciaFiscal("Linha do Siconfi não é um objeto")
        if str(linha.get("cod_conta", "")).strip() != COD_CONTA:
            continue  # elimina intraorçamentárias e outros quadros
        if _limpar(linha.get("coluna")) != _limpar(COLUNA):
            continue  # elimina bimestre isolado, empenhadas, percentuais etc.
        if _limpar(linha.get("conta")).startswith("despesas (exceto intra"):
            totais_nao_intra.append(linha)
        for funcao in encontrados:
            if _limpar(linha.get("conta")) != _limpar(funcao):
                continue  # seleciona só sintética, não soma subfunções
            testes = {
                "exercicio": str(ano), "periodo": str(PERIODO),
                "demonstrativo": "RREO", "anexo": ANEXO,
                "uf": uf, "cod_ibge": str(UF_IBGE[uf][0]),
            }
            for chave, esperado in testes.items():
                obtido = str(linha.get(chave, "")).strip()
                if _limpar(obtido) != _limpar(esperado):
                    raise InconsistenciaFiscal(
                        f"Metadado de {uf}/{ano}/{funcao} incompatível: {chave}={obtido!r}, esperado {esperado!r}"
                    )
            encontrados[funcao].append(linha)
    resultado: list[dict] = []
    for funcao, candidatos in encontrados.items():
        if len(candidatos) != 1:
            raise InconsistenciaFiscal(
                f"{uf}/{ano}: função {funcao} retornou {len(candidatos)} registros sintéticos; esperado 1"
            )
        origem = candidatos[0]
        valor = _decimal(origem.get("valor"))
        resultado.append({
            "uf": uf, "estado": UF_IBGE[uf][1], "ano": ano,
            "funcao": funcao, "codigo_funcao": FUNCOES_CODIGO[funcao],
            "valor_reais": format(valor, "f"),
            "estagio": "despesas liquidadas acumuladas ate o 6o bimestre",
            "periodo": PERIODO, "anexo": ANEXO, "cod_conta": COD_CONTA,
            "abrangencia": "governo estadual/distrital; despesas exceto intraorcamentarias",
            "origem": "Siconfi (declaracao oficial nao auditada)",
            "fonte_url": url, "data_coleta_utc": coletado_em or _utc(),
            "hash_fonte_sha256": hashlib.sha256(
                json.dumps(linhas, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        })
    if len(totais_nao_intra) != 1:
        raise InconsistenciaFiscal(
            f"{uf}/{ano}: total das despesas não intraorçamentárias retornou "
            f"{len(totais_nao_intra)} registros; esperado 1"
        )
    # Testes de metadados também se aplicam ao total do quadro.
    total_linha = totais_nao_intra[0]
    if (str(total_linha.get("uf", "")).strip() != uf
            or str(total_linha.get("cod_ibge", "")).strip() != str(UF_IBGE[uf][0])
            or str(total_linha.get("exercicio", "")).strip() != str(ano)
            or str(total_linha.get("periodo", "")).strip() != str(PERIODO)
            or _limpar(total_linha.get("anexo")) != _limpar(ANEXO)
            or _limpar(total_linha.get("demonstrativo")) != "rreo"):
        raise InconsistenciaFiscal(f"{uf}/{ano}: metadados do total não intraorçamentário inconsistentes")
    total_nao_intra = _decimal(total_linha.get("valor"))
    if sum((Decimal(r["valor_reais"]) for r in resultado), Decimal(0)) > total_nao_intra:
        raise InconsistenciaFiscal(
            f"{uf}/{ano}: soma de funções selecionadas ultrapassa total do quadro não intraorçamentário"
        )
    return resultado


@dataclass
class ResultadoColeta:
    ufs: list[str]
    anos: list[int]
    gerado_em_utc: str
    total_combinacoes: int
    combinacoes_validas: int
    registros_validados: int
    combinacoes_pendentes: list[dict]
    situacao: str
    criterio: str
    fonte: str


def coletar(ufs: list[str], anos: list[int], *, cliente: ClienteSiconfi | None = None,
            usar_cache: bool = True, somente_cache: bool = False) -> ResultadoColeta:
    """Escreve snapshot validado e manifesto separadamente, de forma atômica.

    O cache bruto serve à auditoria/reprocessamento e não é apresentado pela API.
    Uma coleta parcial será marcada como incompleta na interface e no manifesto.
    """
    if not ufs or not anos or any(u not in UF_IBGE for u in ufs) or any(not 2021 <= a <= 2025 for a in anos):
        raise ValueError("Selecione UFs válidas e anos entre 2021 e 2025")
    ufs, anos = sorted(set(ufs)), sorted(set(anos))
    cliente = cliente or ClienteSiconfi()
    pasta = diretorio_siconfi()
    dados: list[dict] = []
    pendencias: list[dict] = []
    for uf in ufs:
        for ano in anos:
            local = pasta / "raw" / uf / f"{ano}.json"
            try:
                if usar_cache and local.exists():
                    cache = json.loads(local.read_text(encoding="utf-8"))
                    if not isinstance(cache.get("items"), list) or not isinstance(cache.get("url"), str):
                        raise FalhaColeta("Cache bruto inválido")
                    linhas, url = cache["items"], cache["url"]
                    timestamp = cache.get("coletado_em_utc")
                elif somente_cache:
                    raise FalhaColeta("Cache local ainda não foi criado")
                else:
                    linhas, url = cliente.buscar(uf, ano)
                    timestamp = _utc()
                    _gravar_atomico(local, json.dumps({
                        "items": linhas, "url": url, "coletado_em_utc": timestamp,
                    }, ensure_ascii=False, indent=2))
                try:
                    registros = normalizar(uf, ano, linhas, url, timestamp)
                except InconsistenciaFiscal:
                    # Um cache inválido não pode bloquear para sempre a reconsulta.
                    # Offline preserva o erro; online tenta buscar uma declaração atualizada.
                    if somente_cache or not (usar_cache and local.exists()):
                        raise
                    linhas, url = cliente.buscar(uf, ano)
                    timestamp = _utc()
                    registros = normalizar(uf, ano, linhas, url, timestamp)
                    _gravar_atomico(local, json.dumps({
                        "items": linhas, "url": url, "coletado_em_utc": timestamp,
                    }, ensure_ascii=False, indent=2))
                dados.extend(registros)
            except (FalhaColeta, InconsistenciaFiscal, OSError, ValueError, requests.RequestException) as erro:
                pendencias.append({"uf": uf, "ano": ano, "motivo": str(erro)})
    combinacoes = len(ufs) * len(anos)
    validas = len(dados) // len(FUNCOES_CODIGO)
    manifesto = ResultadoColeta(
        ufs=ufs, anos=anos, gerado_em_utc=_utc(), total_combinacoes=combinacoes,
        combinacoes_validas=validas, registros_validados=len(dados),
        combinacoes_pendentes=pendencias,
        situacao="completo" if not pendencias else "parcial" if dados else "indisponivel",
        criterio=("RREO Anexo 02, 6º bimestre, DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d), "
                  "linhas sintéticas das funções 06, 10 e 12, excluídas as intraorçamentárias"),
        fonte=DOCUMENTACAO,
    )
    import csv
    from io import StringIO
    saida = StringIO()
    escritor = csv.DictWriter(saida, fieldnames=CAMPOS_EXPORTADOS)
    escritor.writeheader()
    escritor.writerows(dados)
    # Não substituir um snapshot anterior válido por uma coleta completamente vazia.
    pasta.mkdir(parents=True, exist_ok=True)
    with FileLock(str(pasta / "coleta.lock"), timeout=20):
        if dados:
            destino_atual = pasta / "despesas_oficiais.csv"
            if destino_atual.exists():
                # Preserva o snapshot anterior em novas coletas/retificações.
                anterior = pasta / "historico" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8])
                anterior.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destino_atual, anterior / "despesas_oficiais.csv")
                manifesto_antigo = pasta / "manifesto.json"
                if manifesto_antigo.exists():
                    shutil.copy2(manifesto_antigo, anterior / "manifesto.json")
            _gravar_atomico(destino_atual, saida.getvalue())
            _gravar_atomico(pasta / "manifesto.json", json.dumps(asdict(manifesto), ensure_ascii=False, indent=2))
        elif not (pasta / "despesas_oficiais.csv").exists():
            _gravar_atomico(pasta / "manifesto.json", json.dumps(asdict(manifesto), ensure_ascii=False, indent=2))
    return manifesto
