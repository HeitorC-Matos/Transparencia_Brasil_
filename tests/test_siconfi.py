"""Contratos de coleta/validação sem exigir rede real do Siconfi."""
import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.consulta_oficial import filtrar, ler_oficiais, serie, status_base
from services.siconfi import (
    API_BASE, ClienteSiconfi, FalhaColeta, InconsistenciaFiscal, UF_IBGE,
    coletar, normalizar,
)


def linhas_validas(uf="SP", ano=2025, valor_base=100):
    linhas = []
    for i, nome in enumerate(("Educação", "Saúde", "Segurança Pública")):
        linhas.append({
            "uf": uf, "cod_ibge": UF_IBGE[uf][0], "exercicio": ano,
            "periodo": 6, "demonstrativo": "RREO", "anexo": "RREO-Anexo 02",
            "cod_conta": "RREO2TotalDespesas", "conta": nome,
            "coluna": "DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)",
            "valor": valor_base + i,
        })
    linhas.append(dict(linhas[0], conta="DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)",
                       valor=1000000000))
    return linhas


def url(uf="SP", ano=2025):
    return f"{API_BASE}?an_exercicio={ano}&id_ente={UF_IBGE[uf][0]}"


class RespostaFalsa:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests import HTTPError
            raise HTTPError(str(self.status_code))

    def json(self):
        return self.payload


class SessaoFalsa:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def get(self, url, **kw):
        self.chamadas.append((url, kw))
        return self.respostas.pop(0)


def test_normaliza_exatamente_as_tres_funcoes():
    rows = linhas_validas()
    rows.extend([dict(rows[0], cod_conta="RREO2TotalDespesasIntra", valor=5000000),
                 dict(rows[0], conta="Ensino Fundamental", valor=700000),
                 dict(rows[0], coluna="DESPESAS LIQUIDADAS NO BIMESTRE", valor=900000)])
    saida = normalizar("SP", 2025, rows, url())
    assert len(saida) == 3
    assert [r["valor_reais"] for r in saida] == ["100", "101", "102"]
    assert {r["codigo_funcao"] for r in saida} == {"12", "10", "06"}
    assert all("exceto intraorcamentarias" in r["abrangencia"] for r in saida)


def test_sem_linha_sintetica_nao_soma_subfuncoes():
    with pytest.raises(InconsistenciaFiscal, match="retornou 0"):
        normalizar("SP", 2025, linhas_validas()[:2], url())


def test_recusa_duplicidade_contabil():
    rows = linhas_validas()
    with pytest.raises(InconsistenciaFiscal, match="retornou 2"):
        normalizar("SP", 2025, rows + [rows[0]], url())


@pytest.mark.parametrize("chave,valor", [("uf", "GO"), ("exercicio", 2024),
                                        ("periodo", 5), ("cod_ibge", 52),
                                        ("anexo", "RREO-Anexo 01")])
def test_recusa_metadados_incompatíveis(chave, valor):
    rows = linhas_validas()
    rows[0][chave] = valor
    with pytest.raises(InconsistenciaFiscal, match="Metadado"):
        normalizar("SP", 2025, rows, url())


@pytest.mark.parametrize("valor", [None, -50, "NaN", "Infinity", "x", ""])
def test_recusa_valor_invalido(valor):
    rows = linhas_validas()
    rows[0]["valor"] = valor
    with pytest.raises(InconsistenciaFiscal):
        normalizar("SP", 2025, rows, url())


def test_cliente_paginação_e_restricao_host():
    a = {"items": linhas_validas()[:1], "hasMore": True,
         "links": [{"rel": "next", "href": API_BASE + "?offset=1"}]}
    b = {"items": linhas_validas()[1:], "hasMore": False, "links": []}
    sessao = SessaoFalsa([RespostaFalsa(a), RespostaFalsa(b)])
    c = ClienteSiconfi(sessao=sessao, intervalo=0)
    linhas, fonte = c.buscar("SP", 2025)
    assert len(linhas) == 4 and len(sessao.chamadas) == 2
    assert "id_ente=35" in fonte


def test_cliente_recusa_paginacao_externa():
    pag = {"items": [], "hasMore": True,
           "links": [{"rel": "next", "href": "https://example.com/externo"}]}
    with pytest.raises(FalhaColeta, match="inseguro"):
        ClienteSiconfi(sessao=SessaoFalsa([RespostaFalsa(pag)]), intervalo=0).buscar("SP", 2025)


def test_cliente_recusa_paginacao_sem_link():
    pag = {"items": [], "hasMore": True, "links": []}
    with pytest.raises(FalhaColeta, match="next"):
        ClienteSiconfi(sessao=SessaoFalsa([RespostaFalsa(pag)]), intervalo=0).buscar("SP", 2025)


def test_coleta_piloto_cache_e_api_separada(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))
    from shutil import copyfile
    from utils.dados import ROOT
    copyfile(ROOT / "data" / "amostra_dados.csv", tmp_path / "amostra_dados.csv")

    class Cliente:
        chamadas = 0
        def buscar(self, uf, ano):
            self.chamadas += 1
            return linhas_validas(uf, ano), url(uf, ano)

    fonte = Cliente()
    manifesto = coletar(["SP", "GO", "BA"], [2025], cliente=fonte)
    assert manifesto.situacao == "completo"
    assert manifesto.combinacoes_validas == 3
    assert manifesto.registros_validados == 9
    assert fonte.chamadas == 3
    assert len(ler_oficiais()) == 9
    assert len(filtrar(uf="GO", ano=2025)) == 3
    assert len(filtrar(funcao="Educação")) == 3
    cliente_api = TestClient(app)
    r = cliente_api.get("/dados-oficiais", params={"uf": "BA", "ano": 2025})
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert all(row["uf"] == "BA" for row in r.json()["dados"])
    assert cliente_api.get("/despesas").json()["total"] == 9
    # Deve funcionar novamente sem acesso à rede, usando apenas o cache.
    repeticao = coletar(["SP", "GO", "BA"], [2025], cliente=fonte, somente_cache=True)
    assert repeticao.situacao == "completo" and fonte.chamadas == 3


def test_coleta_parcial_distingue_dado_ausente_de_zero(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))

    class Cliente:
        def buscar(self, uf, ano):
            return (linhas_validas(uf, ano) if uf == "SP" else []), url(uf, ano)

    resultado = coletar(["SP", "GO"], [2025], cliente=Cliente())
    assert resultado.situacao == "parcial"
    assert resultado.registros_validados == 3
    assert len(resultado.combinacoes_pendentes) == 1
    status = status_base()
    assert status["situacao"] == "parcial"
    assert len(ler_oficiais()) == 3
    assert not filtrar(uf="GO")


def test_serie_variacao_consecutiva_e_ano_ausente(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))

    class Cliente:
        def buscar(self, uf, ano):
            return linhas_validas(uf, ano, 100 if ano == 2021 else 150), url(uf, ano)

    coletar(["SP"], [2021, 2023], cliente=Cliente())
    resultado = serie("SP", "Educação")
    assert len(resultado) == 2 and resultado[1]["variacao_nominal_percentual"] is None
    coletar(["SP"], [2021, 2022], cliente=Cliente(), usar_cache=False)
    result2 = serie("SP", "Educação")
    assert result2[1]["variacao_nominal_percentual"] == Decimal("50.0000")


def test_rota_sem_coleta_informa_base_ausente(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))
    api = TestClient(app)
    assert api.get("/dados-oficiais/status").json()["situacao"] == "nao_coletado"
    assert api.get("/dados-oficiais").json()["dados"] == []
    assert api.get("/dados-oficiais", params={"ano": 2019}).status_code == 422
    assert api.get("/dados-oficiais/serie", params={"uf": "XX", "funcao": "Saúde"}).status_code == 422


def test_nao_publica_numeros_sem_verificacao(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))
    class Cliente:
        def buscar(self, uf, ano):
            raise FalhaColeta("sem conexão")
    manifesto = coletar(["SP"], [2025], cliente=Cliente())
    assert manifesto.situacao == "indisponivel"
    assert not (tmp_path / "siconfi" / "despesas_oficiais.csv").exists()


def test_critica_reconciliacao_com_total_nao_intra():
    rows = linhas_validas()
    rows[-1]["valor"] = 150
    with pytest.raises(InconsistenciaFiscal, match="ultrapassa"):
        normalizar("SP", 2025, rows, url())


def test_recusa_total_nao_intra_ausente():
    with pytest.raises(InconsistenciaFiscal, match="total das despesas"):
        normalizar("SP", 2025, linhas_validas()[:3], url())


def test_agregados_regionais_nao_somam_regiao_incompleta(tmp_path, monkeypatch):
    monkeypatch.setenv("TP3_DATA_DIR", str(tmp_path))
    from services.consulta_oficial import agregar_regioes
    class Cliente:
        def buscar(self, uf, ano):
            return linhas_validas(uf, ano), url(uf, ano)
    coletar(["SP", "MG", "RJ"], [2025], cliente=Cliente())
    quadro = agregar_regioes(2025, "Saúde")
    sudeste = next(x for x in quadro if x["regiao"] == "Sudeste")
    assert sudeste["ufs_com_dados"] == 3
    assert sudeste["ufs_ausentes"] == ["ES"]
    assert sudeste["valor_reais"] is None
    resposta = TestClient(app).get('/dados-oficiais/regioes',params={'ano':2025,'funcao':'Saúde'})
    assert resposta.status_code == 200
    assert next(x for x in resposta.json()['dados'] if x['regiao']=='Sudeste')['valor_reais'] is None
