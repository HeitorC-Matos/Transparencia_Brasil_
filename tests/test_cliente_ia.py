from utils.api_client import APIIndisponivel, consultar_status_ia, processar_texto_ia
import pytest


class Resposta:
    def __init__(self, data):
        self.data = data
    def raise_for_status(self):
        return None
    def json(self):
        return self.data


class Sessao:
    def __init__(self, data):
        self.data = data
        self.ultimo = None
    def get(self, url, params=None, timeout=None):
        self.ultimo = (url, timeout)
        return Resposta(self.data)
    def post(self, url, json=None, timeout=None):
        self.ultimo = (url, json, timeout)
        return Resposta(self.data)


def test_status_ia_cliente():
    sessao = Sessao({"status": "nao_carregado"})
    assert consultar_status_ia(sessao=sessao)["status"] == "nao_carregado"
    assert sessao.ultimo[1] == 8


def test_processamento_ia_cliente_timeout_proprio():
    sessao = Sessao({"resultado": "Sumário", "execucao_local": True})
    assert processar_texto_ia("Texto de teste", sessao=sessao)["resultado"] == "Sumário"
    assert sessao.ultimo[1]["operacao"] == "resumo"
    assert sessao.ultimo[2] == 300


def test_rejeita_resposta_llm_sem_confirmacao_local():
    sessao = Sessao({"resultado": "Texto", "execucao_local": False})
    with pytest.raises(APIIndisponivel):
        processar_texto_ia("Texto de teste", sessao=sessao)
