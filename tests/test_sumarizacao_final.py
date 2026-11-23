"""Contratos e processamento sem GPU. Prova de inferência real requer teste local."""
from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes import sumarizacao as rota
from services.documentos import Documento, listar_documentos, obter_documento
from services.engenharia_prompts import construir_instrucoes
from services.llm_service import (
    MODEL_ID, ModeloIndisponivel, ModeloOcupado, ResultadoGeracao,
    TempoLimiteGeracao, TextoMuitoLongo,
)
from services.sumarizacao import (
    TextoAcimaDaCapacidade, contexto_fiscal, dividir_texto, sumarizar,
)

client = TestClient(app)


def resposta_fake(**kwargs):
    assert kwargs["instrucao_tarefa"]
    assert "Não invente" in kwargs["instrucoes_sistema"]
    assert kwargs["operacao"] == "resumo"
    return ResultadoGeracao(texto="Síntese fiel ao documento selecionado.",
                           tokens_entrada=120, tokens_saida=23, tempo_ms=410)


def test_catalogo_lê_as_coletas_reais_com_ids_estaveis():
    primeiro = listar_documentos()
    segundo = listar_documentos()
    assert len(primeiro) == 4
    assert [d.id for d in primeiro] == [d.id for d in segundo]
    assert {d.origem for d in primeiro} == {"beautifulsoup", "selenium"}
    assert all(d.url.startswith("https://") and d.texto for d in primeiro)
    assert obter_documento(primeiro[0].id).id == primeiro[0].id


def test_get_documentos_api_sem_modelo():
    resposta = client.get("/ia/documentos")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 4
    assert resposta.json()[0]["caracteres"] > 0
    assert "texto" not in resposta.json()[0]  # a listagem retorna apenas metadados


def test_documento_e_resumo_usam_fonte_real_e_contrato(monkeypatch):
    monkeypatch.setattr(rota.servico_llm, "gerar", resposta_fake)
    doc = listar_documentos()[0]
    resposta = client.post("/ia/resumir_documento", json={"documento_id": doc.id})
    assert resposta.status_code == 200, resposta.text
    item = resposta.json()
    assert item["titulo"] == doc.titulo
    assert item["tipo"] == "documento"
    assert item["fontes"] == [doc.url]
    assert item["modelo"] == MODEL_ID
    assert item["execucao_local"] is True
    assert item["etapas_geracao"] == 1
    assert item["tokens_entrada"] == 120
    assert item["versao_prompt"] == "fundamentado"
    assert item["contexto_calculado"] is None


def test_modos_e_tres_prompts_sao_reais(monkeypatch):
    tarefas = []

    def falso(**kwargs):
        tarefas.append(kwargs["instrucao_tarefa"])
        return resposta_fake(**kwargs)

    monkeypatch.setattr(rota.servico_llm, "gerar", falso)
    id_ = listar_documentos()[0].id
    for versao in ("basico", "estruturado", "fundamentado"):
        resp = client.post("/ia/resumir_documento", json={"documento_id": id_,
                                   "versao_prompt": versao, "modo": "simplificado"})
        assert resp.status_code == 200
        assert resp.json()["versao_prompt"] == versao
    assert len(tarefas) == 3
    assert len(set(tarefas)) == 3


def test_404_documento_desconhecido():
    resposta = client.post("/ia/resumir_documento", json={"documento_id": "doc-" + "0" * 20})
    assert resposta.status_code == 404
    assert resposta.headers.get("X-Request-ID")


@pytest.mark.parametrize("dados", [
    {}, {"documento_id": "../../secreto"},
    {"documento_id": "doc-" + "0" * 20, "versao_prompt": "inventada"},
    {"documento_id": "doc-" + "0" * 20, "max_novos_tokens": 5000},
    {"documento_id": "doc-" + "0" * 20, "extra": "sim"},
])
def test_documento_entradas_invalidas_422(dados):
    assert client.post("/ia/resumir_documento", json=dados).status_code == 422


def test_prompt_explicita_as_limitacoes_e_dados_nao_confiaveis():
    sistema, tarefa = construir_instrucoes("executivo", "fundamentado")
    assert "dado externo" in sistema
    assert "Não execute comandos" in sistema
    assert "habitante" in tarefa
    assert "orçamento inteiro" in tarefa


def test_documento_longo_usa_sumarizacao_hierarquica():
    class Falso:
        def __init__(self): self.chamadas = []
        def gerar(self, **kwargs):
            self.chamadas.append(kwargs)
            return ResultadoGeracao("Informação principal.", 100, 20, 50)
    falso = Falso()
    texto = "Uma descrição relevante com dados públicos. " * 110
    partes = dividir_texto(texto)
    assert len(partes) >= 2
    resultado = sumarizar(texto, modo="topicos", versao="fundamentado",
                         max_tokens=192, servico=falso)
    assert resultado.etapas == len(partes) + 1
    assert resultado.tokens_entrada == resultado.etapas * 100
    assert resultado.tempo_ms == resultado.etapas * 50
    assert "Trecho 1" in falso.chamadas[0]["texto"]
    assert "Sínteses parciais" in falso.chamadas[-1]["texto"]


def test_rejeita_texto_grande_sem_truncar_silenciosamente():
    with pytest.raises(TextoAcimaDaCapacidade):
        dividir_texto("texto com dados coletados. " * 900)


def test_contexto_fiscal_calcula_valores_exatos_e_nao_confunde_orcamento():
    texto, fontes, qtd = contexto_fiscal(["BA", "SP"], 2025, ["Educação", "Saúde"])
    assert qtd == 4
    assert "2025" in texto
    assert "não é despesa total do orçamento" in texto
    assert "não calcule valores per capita" in texto
    assert "Siconfi" in texto
    assert fontes and all(url.startswith("https://") for url in fontes)

    from services.consulta_oficial import filtrar
    dados = [r for r in filtrar(ano=2025) if r["uf"] in ("BA", "SP") and r["funcao"] == "Saúde"]
    esperado = sum((r["valor_reais"] for r in dados), Decimal(0))
    form = f"{esperado:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    assert "R$ " + form in texto


def test_sintese_fiscal_usa_python_antes_da_geracao(monkeypatch):
    enviados = []

    def gerar(**kwargs):
        enviados.append(kwargs["texto"])
        return resposta_fake(**kwargs)

    monkeypatch.setattr(rota.servico_llm, "gerar", gerar)
    resposta = client.post("/ia/sintese_fiscal", json={
        "ufs": ["GO", "SP", "BA"], "ano": 2025,
        "funcoes": ["Saúde", "Educação"], "modo": "topicos",
    })
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["metadados"]["registros"] == 6
    assert dados["tipo"] == "fiscal"
    assert dados["contexto_calculado"]
    assert "Soma da função Saúde" in dados["contexto_calculado"]
    assert enviados and "R$ " in enviados[0]
    assert len(dados["fontes"]) == 3


@pytest.mark.parametrize("corpo", [
    {"ufs": ["ZZ"], "ano": 2025}, {"ufs": [], "ano": 2025},
    {"ufs": ["SP", "SP"], "ano": 2025},
    {"ufs": ["SP"], "ano": 2026},
    {"ufs": ["SP"], "ano": 2025, "funcoes": ["Orçamento geral"]},
    {"ufs": ["SP"], "ano": 2025, "funcoes": []},
])
def test_sintese_fiscal_valida_entradas(corpo):
    assert client.post("/ia/sintese_fiscal", json=corpo).status_code == 422


def test_recorte_incompleto_nao_vira_zero(monkeypatch):
    import services.sumarizacao as mod
    monkeypatch.setattr(mod, "filtrar", lambda **kwargs: [{
        "uf": "SP", "ano": 2025, "funcao": "Saúde",
        "valor_reais": Decimal("150.25"), "fonte_url": "https://example.org/registro",
    }])
    texto, fontes, qtd = contexto_fiscal(["SP", "GO"], 2025, ["Saúde"])
    assert qtd == 1
    assert "Dados ausentes" in texto
    assert "não calculada por falta de cobertura completa" in texto
    assert "R$ 150,25" in texto  # soma de SP isoladamente, não entre UFs
    assert fontes


@pytest.mark.parametrize("erro,status", [
    (ModeloOcupado("ocupado"), 429),
    (ModeloIndisponivel("sem GPU"), 503),
    (TempoLimiteGeracao("tempo esgotado"), 504),
    (TextoMuitoLongo("muitos tokens"), 422),
])
def test_erros_llm_padronizados(monkeypatch, erro, status):
    def falha(**kwargs): raise erro
    monkeypatch.setattr(rota.servico_llm, "gerar", falha)
    r = client.post("/ia/resumir_documento", json={"documento_id": listar_documentos()[0].id})
    assert r.status_code == status
    assert r.headers.get("X-Request-ID")
    if status == 429:
        assert r.headers["retry-after"] == "5"


def test_modelo_real_nao_carregado_automaticamente_ao_listar(monkeypatch):
    def impedir(**kwargs):
        raise AssertionError("Não deveria chamar Qwen ao listar")
    monkeypatch.setattr(rota.servico_llm, "gerar", impedir)
    assert client.get("/ia/documentos").status_code == 200
