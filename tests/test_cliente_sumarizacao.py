"""Cliente HTTP das novas funcionalidades, sem conexão de rede."""
import pytest

from utils.api_client import (
    APIIndisponivel, listar_documentos_ia, resumir_documento_ia,
    sintetizar_dados_fiscais_ia,
)


class FakeResposta:
    def __init__(self, dado): self.dado = dado
    def raise_for_status(self): return None
    def json(self): return self.dado


class FakeSessao:
    def __init__(self, dado): self.dado, self.ultima = dado, None
    def get(self, url, params=None, timeout=0):
        self.ultima = ("GET", url, params, timeout)
        return FakeResposta(self.dado)
    def post(self, url, json=None, timeout=0):
        self.ultima = ("POST", url, json, timeout)
        return FakeResposta(self.dado)


def test_consulta_catalogo():
    fake = FakeSessao([{"id": "doc-123", "titulo": "Título"}])
    assert listar_documentos_ia(sessao=fake)[0]["titulo"] == "Título"
    assert fake.ultima[1].endswith("/ia/documentos")
    assert fake.ultima[3] == 8


def test_cliente_envia_documento_e_timeout():
    fake = FakeSessao({"resultado": "Resumo", "execucao_local": True, "fontes": []})
    assert resumir_documento_ia("doc-123", modo="topicos", sessao=fake)["resultado"] == "Resumo"
    assert fake.ultima[1].endswith("/ia/resumir_documento")
    assert fake.ultima[2]["modo"] == "topicos"
    assert fake.ultima[3] == 300


def test_cliente_fiscal_envia_ufs():
    fake = FakeSessao({"resultado": "Síntese", "execucao_local": True, "fontes": []})
    assert sintetizar_dados_fiscais_ia(["SP", "GO"], 2025, ["Saúde"],
                                     sessao=fake)["resultado"] == "Síntese"
    assert fake.ultima[1].endswith("/ia/sintese_fiscal")
    assert fake.ultima[2]["ufs"] == ["SP", "GO"]


def test_cliente_rejeita_sem_ia_local():
    fake = FakeSessao({"resultado": "Resposta", "execucao_local": False, "fontes": []})
    with pytest.raises(APIIndisponivel):
        resumir_documento_ia("doc-123", sessao=fake)
