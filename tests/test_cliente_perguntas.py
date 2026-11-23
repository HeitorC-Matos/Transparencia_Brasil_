"""Contrato de integração Streamlit > FastAPI para perguntas fiscais."""
import pytest

from utils.api_client import APIIndisponivel, perguntar_dados_ia


class RespostaFalsa:
    def __init__(self, dado): self.dado = dado
    def raise_for_status(self): return None
    def json(self): return self.dado


class SessaoFalsa:
    def __init__(self, dado): self.dado, self.ultima = dado, None
    def post(self, url, json=None, timeout=0):
        self.ultima = (url, json, timeout)
        return RespostaFalsa(self.dado)


def test_cliente_envia_pergunta_ano_e_complemento():
    sessao = SessaoFalsa({"resposta_calculada": "Resultado", "dados": [],
                         "fontes": [], "qwen_executado": True})
    assert perguntar_dados_ia("Quanto GO gastou com saúde?", 2024, sessao=sessao)["resposta_calculada"] == "Resultado"
    assert sessao.ultima[0].endswith("/ia/perguntar_dados")
    assert sessao.ultima[1]["ano_referencia"] == 2024
    assert sessao.ultima[1]["usar_qwen"] is True
    assert sessao.ultima[2] == 300


def test_cliente_pode_consultar_sem_gpu():
    sessao = SessaoFalsa({"resposta_calculada": "Resultado", "dados": [],
                         "fontes": [], "qwen_executado": False})
    perguntar_dados_ia("Quanto GO gastou com saúde?", usar_qwen=False, sessao=sessao)
    assert sessao.ultima[2] == 15


def test_cliente_verifica_contrato():
    sessao = SessaoFalsa({"resultado": "texto sem fonte"})
    with pytest.raises(APIIndisponivel):
        perguntar_dados_ia("Quanto GO gastou com saúde?", sessao=sessao)
