"""Testes de contrato e orquestração, NÃO são prova de inferência na GPU.

O teste real separado é scripts/teste_llm_http_real.py no Windows do usuário.
"""
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.main import app
from api.routes.ia import servico_llm
from services.llm_service import (
    MODEL_ID, ModeloIndisponivel, ModeloOcupado, ResultadoGeracao,
    ServicoLLM, TextoMuitoLongo,
)

cliente = TestClient(app)
PAYLOAD = {"texto": "O projeto utiliza dados acadêmicos ilustrativos.",
           "operacao": "resumo", "max_novos_tokens": 128}


def test_status_nunca_carrega_automaticamente(tmp_path, monkeypatch):
    objeto = ServicoLLM(caminho=tmp_path / "vazio")
    monkeypatch.setattr("api.routes.ia.servico_llm", objeto)
    resposta = cliente.get("/ia/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "arquivos_ausentes"
    assert resposta.json()["execucao_local"] is True


def test_api_invalida_requisicoes_antes_do_modelo():
    for corpo in ({"texto": " "}, {"texto": "a", "operacao": "sentimento"},
                  {"texto": "a", "max_novos_tokens": 9999}, {"texto": "a", "outro": 4},
                  {"operacao": "resumo"}):
        resposta = cliente.post("/processar_texto", json=corpo)
        assert resposta.status_code == 422


def test_quando_modelo_nao_existe_responde_503(tmp_path, monkeypatch):
    monkeypatch.setattr("api.routes.ia.servico_llm", ServicoLLM(caminho=tmp_path / "modelo"))
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 503
    assert "modelo" in resposta.json()["detail"].lower()
    assert cliente.get("/health").status_code == 200


def test_geracao_de_resposta_estruturada_com_servico_injetado(monkeypatch):
    # Simula somente o MOTOR; FastAPI, Pydantic e HTTP permanecem reais.
    def simular_geracao(**kwargs):
        assert kwargs["operacao"] == "resumo"
        return ResultadoGeracao(texto="É uma amostra ilustrativa.",
                               tokens_entrada=35, tokens_saida=10, tempo_ms=120)
    monkeypatch.setattr(servico_llm, "gerar", simular_geracao)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["modelo"] == MODEL_ID
    assert dados["operacao"] == "resumo"
    assert dados["texto_original"] == PAYLOAD["texto"]
    assert dados["resultado"] == "É uma amostra ilustrativa."
    assert dados["execucao_local"] is True
    assert dados["tokens_saida"] == 10
    assert "aviso" in dados


def test_texto_excede_limite_de_tokens(monkeypatch):
    def falhar(**kwargs):
        raise TextoMuitoLongo("Texto longo")
    monkeypatch.setattr(servico_llm, "gerar", falhar)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "Texto longo"


def test_modelo_ocupado_retorna_429(monkeypatch):
    def falhar(**kwargs):
        raise ModeloOcupado("Outro processamento")
    monkeypatch.setattr(servico_llm, "gerar", falhar)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 429
    assert resposta.headers["retry-after"] == "5"


def test_modelo_indisponivel_retorna_503(monkeypatch):
    def falhar(**kwargs):
        raise ModeloIndisponivel("Sem CUDA")
    monkeypatch.setattr(servico_llm, "gerar", falhar)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 503
    assert "CUDA" in resposta.json()["detail"]


def test_excecao_inesperada_nao_vaza_detalhes(monkeypatch):
    def falhar(**kwargs):
        raise RuntimeError("tokens-segredos-exemplo")
    monkeypatch.setattr(servico_llm, "gerar", falhar)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == 500
    assert "tokens-segredos-exemplo" not in resposta.text


def test_trava_impede_requisicoes_concorrentes():
    servico = ServicoLLM()
    assert servico._generation_lock.acquire(blocking=False)
    try:
        import pytest
        with pytest.raises(ModeloOcupado):
            servico.gerar("a", "resumo")
    finally:
        servico._generation_lock.release()


def test_modelo_nao_usa_nuvem_ao_carregar_sem_arquivos(tmp_path, monkeypatch):
    servico = ServicoLLM(caminho=tmp_path / "modelo")
    import pytest
    with pytest.raises(ModeloIndisponivel):
        servico.carregar()
    assert not (tmp_path / "modelo").exists()
