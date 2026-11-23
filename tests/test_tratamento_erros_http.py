"""Tratamento real de HTTP, usando apenas um motor LLM simulado."""
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient

from api.main import app
from api.routes import ia as rotas_ia
from services import llm_service as modulo_llm
from services.llm_service import (
    MemoriaInsuficiente, ModeloIndisponivel, ModeloOcupado,
    ServicoLLM, TempoLimiteGeracao,
)
from utils.api_client import APIIndisponivel, requisitar

cliente = TestClient(app)
PAYLOAD = {"texto": "O orçamento público deve ser transparente.", "operacao": "resumo"}


def test_entrada_invalida_422_tem_erro_estruturado_e_id(monkeypatch):
    monkeypatch.setattr(rotas_ia.servico_llm, "gerar",
                        lambda **kwargs: pytest.fail("GPU não deve ser acionada"))
    resposta = cliente.post("/processar_texto", json={"texto": "  "})
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["erro"]["codigo"] == "ENTRADA_INVALIDA"
    assert corpo["erro"]["requisicao_id"] == resposta.headers["X-Request-ID"]
    assert any("texto" in detalhe["campo"] for detalhe in corpo["erro"]["detalhes"])
    assert isinstance(corpo["detail"], list)
    assert "input" not in str(corpo)


@pytest.mark.parametrize("exc,status,codigo", [
    (ModeloOcupado("Modelo ocupado"), 429, "MODELO_OCUPADO"),
    (ModeloIndisponivel("Sem CUDA"), 503, "MODELO_INDISPONIVEL"),
    (MemoriaInsuficiente("Sem VRAM"), 503, "MODELO_INDISPONIVEL"),
    (TempoLimiteGeracao("Geração muito lenta"), 504, "TEMPO_LIMITE"),
    (RuntimeError("senha-interna-nunca-expor"), 500, "ERRO_INTERNO"),
])
def test_erros_de_inferencia_tem_status_identificador_e_mensagem(monkeypatch, exc, status, codigo):
    def falhar(**kwargs):
        raise exc

    monkeypatch.setattr(rotas_ia.servico_llm, "gerar", falhar)
    resposta = cliente.post("/processar_texto", json=PAYLOAD)
    assert resposta.status_code == status
    assert resposta.json()["erro"]["codigo"] == codigo
    assert resposta.json()["erro"]["mensagem"]
    assert resposta.json()["erro"]["requisicao_id"] == resposta.headers["X-Request-ID"]
    assert "senha-interna-nunca-expor" not in resposta.text
    if status == 429:
        assert resposta.headers["Retry-After"] == "5"
    assert cliente.get("/health").status_code == 200


def test_rota_inexistente_nao_expoe_traceback():
    resposta = cliente.get("/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "NAO_ENCONTRADO"
    assert "traceback" not in resposta.text.lower()


def test_openapi_documenta_cenarios_de_erro():
    rota = cliente.get("/openapi.json").json()["paths"]["/processar_texto"]["post"]
    assert {"200", "422", "429", "500", "503", "504"} <= set(rota["responses"])
    for codigo in ("422", "429", "500", "503", "504"):
        assert "schema" in rota["responses"][codigo]["content"]["application/json"]


class RespostaHTTP:
    def __init__(self, status, body):
        self.status_code = status
        self.body = body
        self.headers = {"X-Request-ID": "req-local-123", "Retry-After": "5"}

    def raise_for_status(self):
        raise requests.HTTPError("Falha", response=self)

    def json(self):
        return self.body


class SessaoHTTP:
    def __init__(self, response):
        self.response = response

    def post(self, *args, **kwargs):
        return self.response


def test_cliente_http_429_exibe_orientacao_sem_mensagem_crua():
    resposta = RespostaHTTP(429, {
        "erro": {"codigo": "MODELO_OCUPADO", "mensagem": "Aguarde", "requisicao_id": "req-local-123"},
        "detail": "O modelo está processando outra solicitação",
    })
    with pytest.raises(APIIndisponivel) as exc:
        requisitar("POST", "/processar_texto", json=PAYLOAD, sessao=SessaoHTTP(resposta))
    assert exc.value.status_code == 429
    assert exc.value.requisicao_id == "req-local-123"
    assert exc.value.retry_after == "5"
    assert "aguarde" in str(exc.value).lower()
    assert "Client Error" not in str(exc.value)


def test_cliente_sem_json_de_erro_nao_expoe_erro_bruto():
    resposta = RespostaHTTP(503, {"detail": "Sem CUDA"})
    with pytest.raises(APIIndisponivel) as exc:
        requisitar("POST", "/processar_texto", sessao=SessaoHTTP(resposta))
    assert "modelo de IA" in str(exc.value)


def test_trava_e_geracao_timeout_cooperativo(monkeypatch):
    class FakeTokenizer:
        eos_token_id = 0
        def apply_chat_template(self, *args, **kwargs):
            return "prompt"
        def __call__(self, *args, **kwargs):
            class Entradas(dict):
                def to(self, device):
                    return self
            return Entradas(input_ids=SimpleNamespace(shape=(1, 3)))
        def decode(self, tokens, **kwargs):
            return "Resposta simulada"
    class FakeModel:
        device = "cuda:0"
        def generate(self, **kwargs):
            assert kwargs["max_time"] == 30
            return [[1, 2, 3, 4]]
    servico = ServicoLLM()
    servico._max_generation_seconds = 30
    servico._tokenizer = FakeTokenizer()
    servico._model = FakeModel()
    servico._torch = SimpleNamespace(inference_mode=lambda: nullcontext())
    tempos = iter([100.0, 135.0])
    monkeypatch.setattr(modulo_llm, "perf_counter", lambda: next(tempos))
    with pytest.raises(TempoLimiteGeracao):
        servico.gerar("Texto", "resumo")
    assert servico._generation_lock.acquire(blocking=False)
    servico._generation_lock.release()


def test_falha_cuda_sem_memoria_e_tratada_e_libera_trava():
    class FakeTokenizer:
        eos_token_id = 0
        def apply_chat_template(self, *args, **kwargs):
            return "prompt"
        def __call__(self, *args, **kwargs):
            class Entradas(dict):
                def to(self, device):
                    return self
            return Entradas(input_ids=SimpleNamespace(shape=(1, 3)))
    class FakeModel:
        device = "cuda:0"
        def generate(self, **kwargs):
            raise RuntimeError("CUDA out of memory")
    limpezas = []
    servico = ServicoLLM()
    servico._tokenizer = FakeTokenizer()
    servico._model = FakeModel()
    servico._torch = SimpleNamespace(
        inference_mode=lambda: nullcontext(),
        cuda=SimpleNamespace(empty_cache=lambda: limpezas.append(True)),
    )
    with pytest.raises(MemoriaInsuficiente):
        servico.gerar("Texto", "resumo")
    assert limpezas == [True]
    assert servico._generation_lock.acquire(blocking=False)
    servico._generation_lock.release()


def test_cliente_indisponibilidade_dados_oficiais_nao_cita_qwen():
    resposta = RespostaHTTP(503, {
        "erro": {"codigo": "BASE_OFICIAL_INDISPONIVEL", "mensagem": "Base indisponível"},
    })
    with pytest.raises(APIIndisponivel) as exc:
        requisitar("POST", "/dados-oficiais/status", sessao=SessaoHTTP(resposta))
    assert "Siconfi" in str(exc.value)
    assert "Qwen" not in str(exc.value)
