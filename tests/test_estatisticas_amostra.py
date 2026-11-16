"""Testes dos indicadores apresentados na página de Estatísticas."""

import pandas as pd
import pytest

from utils.dados import ler_amostra
from utils.estatisticas_amostra import (
    classificar_estados, comparar_estados, composicao_funcoes,
    estatisticas_por_funcao, matriz_funcoes, per_capita_funcoes,
    resumo_estados, validar_amostra,
)


@pytest.fixture
def amostra():
    # Carrega somente o CSV ilustrativo, nunca a base oficial nem cadastros manuais.
    return ler_amostra()


def test_validar_nao_modifica_dataframe_original(amostra):
    original = amostra.copy(deep=True)
    assert len(validar_amostra(amostra)) == 9
    pd.testing.assert_frame_equal(amostra, original)


def test_totais_tres_estados_e_populacao_nao_somada(amostra):
    r = resumo_estados(amostra).set_index("sigla")
    assert r.loc["SP", "total"] == 75_000_000_000
    assert r.loc["GO", "total"] == 17_600_000_000
    assert r.loc["BA", "total"] == 27_400_000_000
    assert r.loc["SP", "populacao"] == 45_900_000
    assert r.loc["SP", "valor_por_habitante"] == pytest.approx(75e9 / 45_900_000)


def test_participacao_pct_denominador_eh_soma_tres_funcoes(amostra):
    pct = composicao_funcoes(amostra)
    sp = pct[pct["sigla"].eq("SP")].set_index("funcao")
    assert sp.loc["Educação", "participacao_pct"] == pytest.approx(32 / 75 * 100)
    assert sp.loc["Saúde", "participacao_pct"] == pytest.approx(28.5 / 75 * 100)
    assert sp["participacao_pct"].sum() == pytest.approx(100)
    assert pct.groupby("sigla")["participacao_pct"].sum().to_list() == pytest.approx([100, 100, 100])


def test_por_habitante_em_cada_funcao(amostra):
    tab = per_capita_funcoes(amostra)
    educ_go = tab.loc[(tab["sigla"] == "GO") & (tab["funcao"] == "Educação")].iloc[0]
    assert educ_go["valor_por_habitante"] == pytest.approx(7_200_000_000 / 7_350_000)


def test_ranking_total_e_ranking_per_capita(amostra):
    assert classificar_estados(amostra)["sigla"].to_list() == ["SP", "BA", "GO"]
    assert classificar_estados(amostra, criterio="valor_por_habitante")["sigla"].to_list() == ["GO", "BA", "SP"]
    assert classificar_estados(amostra, funcao="Saúde")["sigla"].to_list() == ["SP", "BA", "GO"]


def test_comparacao_direcional_valor_e_por_habitante(amostra):
    comp = comparar_estados(amostra, "Goiás", "Bahia", funcao="Saúde")
    assert comp["valor_absoluto"]["a"] == 6_100_000_000
    assert comp["valor_absoluto"]["b"] == 10_200_000_000
    assert comp["valor_absoluto"]["diferenca"] == 4_100_000_000
    assert comp["valor_absoluto"]["diferenca_pct"] == pytest.approx(4.1 / 6.1 * 100)
    assert comp["por_habitante"]["diferenca"] == pytest.approx(
        10_200_000_000 / 14_900_000 - 6_100_000_000 / 7_350_000
    )


def test_comparacao_estados_iguais_eh_recusada(amostra):
    with pytest.raises(ValueError, match="diferentes"):
        comparar_estados(amostra, "São Paulo", "São Paulo")


def test_matriz_sem_zeros_artificiais(amostra):
    sem_bahia_saude = amostra.loc[~((amostra["sigla"] == "BA") & (amostra["funcao"] == "Saúde"))].copy()
    matriz = matriz_funcoes(sem_bahia_saude)
    assert pd.isna(matriz.loc["Bahia", "Saúde"])
    assert matriz.loc["São Paulo", "Saúde"] == 28_500_000_000
    assert matriz_funcoes(amostra, "valor_por_habitante").loc["Bahia", "Saúde"] == pytest.approx(10.2e9/14.9e6)


def test_estatisticas_descritivas_amplitude(amostra):
    r = estatisticas_por_funcao(amostra).set_index("funcao")
    assert r.loc["Educação", "media"] == pytest.approx((32 + 7.2 + 11.5) * 1e9 / 3)
    assert r.loc["Educação", "mediana"] == 11_500_000_000
    assert r.loc["Educação", "amplitude"] == 32_000_000_000 - 7_200_000_000
    assert r.loc["Educação", "estados"] == 3


def test_entrada_duplicada_eh_recusada(amostra):
    duplicada = pd.concat([amostra, amostra.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicados"):
        validar_amostra(duplicada)


def test_populacao_inconsistente_eh_recusada(amostra):
    incorreta = amostra.copy()
    incorreta.loc[1, "populacao"] += 100
    with pytest.raises(ValueError, match="populações diferentes"):
        validar_amostra(incorreta)


def test_valores_invalidos_sao_recusados(amostra):
    for campo, valor in [("populacao", 0), ("valor_despesa", -1), ("valor_despesa", float("nan")), ("ano", 2025.5)]:
        incorreta = amostra.copy()
        if campo == "ano":
            incorreta[campo] = incorreta[campo].astype(float)
        incorreta.loc[0, campo] = valor
        with pytest.raises(ValueError):
            validar_amostra(incorreta)


def test_zero_em_todas_as_funcoes_nao_inventa_percentual(amostra):
    zero = amostra.copy()
    zero["valor_despesa"] = 0
    assert composicao_funcoes(zero)["participacao_pct"].isna().all()
    comparacao = comparar_estados(zero, "Goiás", "Bahia")
    assert comparacao["valor_absoluto"]["diferenca_pct"] is None


def test_tela_consulta_somente_amostra():
    from pathlib import Path
    pag = (Path(__file__).resolve().parents[1] / "pages" / "4_Estatisticas.py").read_text(encoding="utf-8")
    assert 'consultar_despesas(origem="amostra_academica")' in pag
    assert "consultar_dados_oficiais" not in pag
    assert "registros_manuais" not in pag
