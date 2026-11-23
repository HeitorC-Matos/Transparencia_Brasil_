from utils.analises import formatar_reais, gasto_por_habitante, palavras_frequentes
from utils.dados import ler_amostra


def test_formatacao():
    assert formatar_reais(1234567.89) == "R$ 1.234.567,89"


def test_populacao_nao_e_somada(dados_isolados):
    df = ler_amostra()
    tabela = gasto_por_habitante(df)
    sp = tabela.loc[tabela["estado"] == "São Paulo"].iloc[0]
    assert sp["populacao"] == 45900000
    assert sp["total"] == 32000000000 + 28500000000 + 14500000000


def test_palavras_sem_stopwords():
    freq = dict(palavras_frequentes(["Educação para pessoas. Educação e saúde."]))
    assert freq["educação"] == 2
    assert "para" not in freq
