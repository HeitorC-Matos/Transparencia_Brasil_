"""Verificações do padrão de geração de 384 tokens."""
from api.schemas.ia import RequisicaoTexto
from api.schemas.perguntas import RequisicaoPergunta
from api.schemas.sumarizacao import ConfiguracaoResumo
from services.engenharia_prompts import MODOS


def test_padrao_sumarizacao_384():
    assert ConfiguracaoResumo().max_novos_tokens == 384


def test_padrao_texto_livre_384():
    assert RequisicaoTexto(texto="Exemplo de transparência pública.").max_novos_tokens == 384


def test_padrao_pergunta_384():
    assert RequisicaoPergunta(pergunta="Qual o maior gasto em Saúde?").max_novos_tokens == 384


def test_prompt_executivo_retorna_ao_formato_original():
    assert MODOS["executivo"] == "Escreva um resumo executivo objetivo, em até três parágrafos."
