"""Validação de contratos HTTP/Pydantic — não exige GPU nem modelo baixado."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from api.schemas.geral import ConteudoWeb, ResumoEstatisticas, SaudeAPI
from api.schemas.ia import RequisicaoTexto, RespostaTexto, StatusModelo
from api.routes import ia as rotas_ia
from services.llm_service import ResultadoGeracao

cliente = TestClient(app)
SEM_PROPAGAR_EXCECAO = TestClient(app, raise_server_exceptions=False)

REQUISICAO = {
    "texto": "A transparência pública favorece o controle social.",
    "operacao": "resumo",
    "max_novos_tokens": 128,
}


def exemplo_resposta():
    return {
        "operacao": "resumo", "texto_original": REQUISICAO["texto"],
        "resultado": "A transparência pública favorece o controle social.",
        "modelo": "Qwen/Qwen3-4B-Instruct-2507", "execucao_local": True,
        "tokens_entrada": 55, "tokens_saida": 12,
        "tempo_processamento_ms": 120, "aviso": "Confira a resposta antes de utilizá-la.",
    }


@pytest.mark.parametrize("mudancas", [
    {"texto": ""},
    {"texto": "  \n  "},
    {"texto": "\u200b\u200c"},
    {"texto": "...?!"},
    {"texto": "a" * 12001},
    {"texto": 123},
    {"texto": ["a", "b"]},
    {"operacao": "sentimento"},
    {"operacao": 5},
    {"max_novos_tokens": 31},
    {"max_novos_tokens": 513},
    {"max_novos_tokens": "128"},
    {"max_novos_tokens": 128.5},
    {"max_novos_tokens": True},
    {"campo_inesperado": "não permitido"},
])
def test_entrada_invalida_rejeitada_sem_chamar_llm(mudancas, monkeypatch):
    def proibido(**kwargs):
        raise AssertionError("A entrada inválida não deve acionar a GPU")

    monkeypatch.setattr(rotas_ia.servico_llm, "gerar", proibido)
    corpo = {**REQUISICAO, **mudancas}
    resposta = cliente.post("/processar_texto", json=corpo)
    assert resposta.status_code == 422
    assert isinstance(resposta.json().get("detail"), list)


def test_ausencia_de_campo_obrigatorio_422():
    corpo = {k: v for k, v in REQUISICAO.items() if k != "texto"}
    resposta = cliente.post("/processar_texto", json=corpo)
    assert resposta.status_code == 422


def test_entrada_valida_com_acentos_e_espacos_aplica_normalizacao(monkeypatch):
    observado = []

    def simular(**kwargs):
        observado.append(kwargs)
        return ResultadoGeracao("Resumo válido.", 40, 8, 34)

    monkeypatch.setattr(rotas_ia.servico_llm, "gerar", simular)
    resposta = cliente.post("/processar_texto", json={
        "texto": "  Educação e saúde são funções orçamentárias. \n",
        "operacao": "explicacao",
    })
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["operacao"] == "explicacao"
    assert corpo["texto_original"] == "Educação e saúde são funções orçamentárias."
    assert corpo["resultado"] == "Resumo válido."
    assert observado[0]["texto"] == corpo["texto_original"]
    assert observado[0]["max_novos_tokens"] == 384
    assert RespostaTexto.model_validate(corpo).execucao_local is True


def test_tipo_booleano_nao_e_numero_inteiro_na_saida():
    dados = exemplo_resposta()
    dados["tokens_saida"] = True
    with pytest.raises(ValidationError):
        RespostaTexto.model_validate(dados)


@pytest.mark.parametrize("campo,valor", [
    ("resultado", ""), ("resultado", "  \n  "),
    ("texto_original", ""), ("modelo", ""),
    ("tokens_entrada", 0), ("tokens_saida", -1),
    ("tempo_processamento_ms", -1), ("tokens_saida", "12"),
    ("tempo_processamento_ms", 5.1),
    ("execucao_local", False), ("execucao_local", "true"),
    ("aviso", ""),
])
def test_modelo_de_resposta_recusa_dados_invalidos(campo, valor):
    dados = exemplo_resposta()
    dados[campo] = valor
    with pytest.raises(ValidationError):
        RespostaTexto.model_validate(dados)


def test_modelo_de_resposta_recusa_campos_extras():
    with pytest.raises(ValidationError):
        RespostaTexto.model_validate({**exemplo_resposta(), "token_privado": "não"})


def test_modelo_de_requisicao_recusa_campos_extras():
    with pytest.raises(ValidationError):
        RequisicaoTexto.model_validate({**REQUISICAO, "debug": True})


def test_resposta_invalida_nao_e_entregue_ao_cliente_como_200(monkeypatch):
    def resposta_vazia(**kwargs):
        return ResultadoGeracao("  ", 33, 1, 10)

    monkeypatch.setattr(rotas_ia.servico_llm, "gerar", resposta_vazia)
    resposta = SEM_PROPAGAR_EXCECAO.post("/processar_texto", json=REQUISICAO)
    assert resposta.status_code == 500
    assert "  " not in resposta.text
    assert "traceback" not in resposta.text.lower()


def test_status_modelo_exige_formato_esperado():
    with pytest.raises(ValidationError):
        StatusModelo.model_validate({
            "status": "outro", "modelo": "modelo", "execucao_local": True,
            "caminho_modelo": "/tmp", "detalhe": "teste",
        })


def test_modelos_das_rotas_gerais_validam_respostas(dados_isolados):
    for caminho, modelo in (
        ("/health", SaudeAPI),
        ("/estatisticas", ResumoEstatisticas),
    ):
        resposta = cliente.get(caminho)
        assert resposta.status_code == 200
        modelo.model_validate(resposta.json())
    conteudo = cliente.get("/conteudo-web")
    assert conteudo.status_code == 200
    for registro in conteudo.json():
        ConteudoWeb.model_validate(registro)


def test_estatisticas_recusa_total_invalido():
    with pytest.raises(ValidationError):
        ResumoEstatisticas.model_validate({
            "origem": "amostra_academica", "quantidade": 3,
            "total_valor_despesa": float("inf"),
            "totais_por_funcao": {"Saúde": 10},
            "aviso": "Amostra ilustrativa.",
        })


def test_web_recusa_url_ou_texto_invalidos():
    with pytest.raises(ValidationError):
        ConteudoWeb.model_validate({
            "titulo": "Documento", "url": "javascript:alert(1)",
            "texto": "", "data_coleta": "hoje", "metodo": "coleta",
        })


def test_openapi_declara_contratos_de_todas_as_rotas():
    especificacao = cliente.get("/openapi.json")
    assert especificacao.status_code == 200
    caminhos = especificacao.json()["paths"]
    for rota, metodos in (
        ("/health", ("get",)),
        ("/despesas", ("get", "post")),
        ("/estatisticas", ("get",)),
        ("/conteudo-web", ("get",)),
        ("/ia/health", ("get",)),
        ("/processar_texto", ("post",)),
        ("/dados-oficiais", ("get",)),
        ("/dados-oficiais/status", ("get",)),
        ("/dados-oficiais/serie", ("get",)),
        ("/dados-oficiais/regioes", ("get",)),
    ):
        for metodo in metodos:
            resposta_200 = caminhos[rota][metodo]["responses"]
            chave = "201" if (rota, metodo) == ("/despesas", "post") else "200"
            assert "schema" in resposta_200[chave]["content"]["application/json"]

    req = especificacao.json()["components"]["schemas"]["RequisicaoTexto"]
    resp = especificacao.json()["components"]["schemas"]["RespostaTexto"]
    assert "texto" in req["required"]
    assert {"operacao", "texto_original", "resultado", "modelo", "execucao_local",
            "tokens_entrada", "tokens_saida", "tempo_processamento_ms", "aviso"} <= set(resp["required"])
    assert req["additionalProperties"] is False
    assert resp["additionalProperties"] is False
