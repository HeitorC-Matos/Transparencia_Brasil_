"""Valida os indicadores nacionais, sem GPU, internet ou mudanças na coleta Siconfi."""

from pathlib import Path

import pandas as pd
import pytest

from services.siconfi import FUNCOES_CODIGO, REGIOES, UF_IBGE
from utils.estatisticas_oficiais import (
    FUNCOES, agregar_ufs, agregacao_regional, comparar, composicao, descricao,
    historico, selecionar, validar_oficiais,
)

ROOT = Path(__file__).resolve().parents[1]


def linha(uf="SP", ano=2025, funcao="Educação", valor=100):
    return {
        "uf": uf, "estado": UF_IBGE[uf][1], "ano": ano, "funcao": funcao,
        "codigo_funcao": FUNCOES_CODIGO[funcao], "valor_reais": valor,
        "periodo": 6, "cod_conta": "RREO2TotalDespesas",
        "fonte_url": "https://apidatalake.tesouro.gov.br/consulta",
    }


@pytest.fixture
def exemplo():
    return validar_oficiais(pd.DataFrame([
        linha("SP", 2024, "Educação", 50),
        linha("SP", 2024, "Saúde", 60),
        linha("SP", 2024, "Segurança Pública", 40),
        linha("SP", 2025, "Educação", 100),
        linha("SP", 2025, "Saúde", 200),
        linha("SP", 2025, "Segurança Pública", 50),
        linha("BA", 2025, "Educação", 70),
        linha("BA", 2025, "Saúde", 30),
        linha("BA", 2025, "Segurança Pública", 10),
        linha("GO", 2025, "Educação", 0),
        linha("GO", 2025, "Saúde", 0),
        linha("GO", 2025, "Segurança Pública", 0),
    ]))


def test_valida_sem_modificar_dados(exemplo):
    copia = exemplo.copy(deep=True)
    pd.testing.assert_frame_equal(validar_oficiais(exemplo), copia)


def test_agregado_completo_ano_2025(exemplo):
    agregado, pendentes = agregar_ufs(exemplo, ano=2025, ufs=["BA", "SP", "GO"], funcoes=list(FUNCOES))
    assert pendentes == []
    assert agregado["uf"].tolist() == ["SP", "BA", "GO"]
    assert agregado["valor_reais"].tolist() == pytest.approx([350, 110, 0])
    assert len(selecionar(exemplo, ano=2025, ufs=["BA", "SP"], funcoes=["Saúde"])) == 2


def test_funcao_individual_e_selecao_uma_uf(exemplo):
    agregado, pendentes = agregar_ufs(exemplo, ano=2025, ufs=["BA"], funcoes=["Saúde"])
    assert pendentes == [] and agregado.iloc[0]["valor_reais"] == 30


def test_ausencia_nao_virou_zero(exemplo):
    sem_sp = exemplo.loc[~((exemplo["uf"] == "SP") & (exemplo["ano"] == 2025)
                            & (exemplo["funcao"] == "Saúde"))]
    agregado, pendentes = agregar_ufs(sem_sp, ano=2025, ufs=["SP", "BA", "GO"], funcoes=list(FUNCOES))
    assert "SP" not in set(agregado["uf"])
    assert pendentes == [{"uf": "SP", "funcoes_ausentes": ["Saúde"]}]
    assert composicao(sem_sp, ano=2025, uf="SP").empty
    with pytest.raises(ValueError, match="Saúde"):
        comparar(sem_sp, ano=2025, uf_a="SP", uf_b="BA", funcoes=list(FUNCOES))


def test_composicao_com_denominador_correto(exemplo):
    fatia = composicao(exemplo, ano=2025, uf="SP").set_index("funcao")
    assert fatia.loc["Saúde", "participacao_pct"] == pytest.approx(200 / 350 * 100)
    assert fatia["participacao_pct"].sum() == pytest.approx(100)
    assert pd.isna(composicao(exemplo, ano=2025, uf="GO")["participacao_pct"]).all()


def test_comparacao_e_referencia_zero(exemplo):
    d = comparar(exemplo, ano=2025, uf_a="BA", uf_b="SP", funcoes=list(FUNCOES))
    assert d["valor_a"] == 110 and d["valor_b"] == 350
    assert d["diferenca_reais"] == 240
    assert d["diferenca_pct"] == pytest.approx(240 / 110 * 100)
    assert comparar(exemplo, ano=2025, uf_a="GO", uf_b="BA", funcoes=list(FUNCOES))["diferenca_pct"] is None
    with pytest.raises(ValueError, match="diferentes"):
        comparar(exemplo, ano=2025, uf_a="SP", uf_b="SP", funcoes=list(FUNCOES))


def test_historico_variacao_e_ano_ausente(exemplo):
    h = historico(exemplo, ufs=["SP", "BA"], funcoes=["Educação"]).set_index(["uf", "ano"])
    assert h.loc[("SP", 2025), "variacao_nominal_pct"] == pytest.approx(100)
    assert pd.isna(h.loc[("BA", 2025), "variacao_nominal_pct"])
    sem_2024 = exemplo.loc[~((exemplo["uf"] == "SP") & exemplo["ano"].eq(2024))]
    assert pd.isna(historico(sem_2024, ufs=["SP"], funcoes=["Educação"]).iloc[0]["variacao_nominal_pct"])


def test_descritivas_somente_registros_completos(exemplo):
    ag, _ = agregar_ufs(exemplo, ano=2025, ufs=["SP", "BA", "GO"], funcoes=list(FUNCOES))
    s = descricao(ag)
    assert s["quantidade_ufs"] == 3
    assert s["media"] == pytest.approx(460 / 3)
    assert s["mediana"] == 110
    assert s["amplitude"] == 350
    assert descricao(ag.iloc[0:0]) is None


def test_regioes_so_se_todas_ufs_presentes(exemplo):
    agregado, _ = agregar_ufs(exemplo, ano=2025, ufs=["SP", "BA", "GO"], funcoes=list(FUNCOES))
    regional = agregacao_regional(agregado, ["SP", "BA", "GO"])
    assert regional["situacao"].eq("incompleto").all()
    assert regional["valor_reais"].isna().all()
    # Com cobertura total, um valor regional zero é possível e válido.
    todas = pd.DataFrame({"uf": list(UF_IBGE), "valor_reais": [0] * len(UF_IBGE)})
    regiao = agregacao_regional(todas, list(UF_IBGE))
    assert regiao["situacao"].eq("completo").all()
    assert regiao["valor_reais"].eq(0).all()
    assert sum(map(len, REGIOES.values())) == 27


@pytest.mark.parametrize("campo,valor", [
    ("valor_reais", -1), ("valor_reais", float("nan")),
    ("valor_reais", float("inf")), ("periodo", 5),
    ("ano", 2020), ("ano", 2024.5),
    ("uf", "XX"), ("codigo_funcao", "09"),
    ("cod_conta", "RREO2TotalDespesasIntra"),
    ("fonte_url", ""), ("estado", "Outro"),
])
def test_recusa_registro_invalido(exemplo, campo, valor):
    dados = exemplo.copy(deep=True)
    if campo == "ano":
        dados[campo] = dados[campo].astype(float)
    dados.loc[0, campo] = valor
    with pytest.raises(ValueError):
        validar_oficiais(dados)


def test_recusa_duplicatas_e_coluna_ausente(exemplo):
    with pytest.raises(ValueError, match="duplicados"):
        validar_oficiais(pd.concat([exemplo, exemplo.iloc[[0]]]))
    with pytest.raises(ValueError, match="Colunas ausentes"):
        validar_oficiais(exemplo.drop(columns=["fonte_url"]))


def test_fonte_nacional_abrange_27_ufs_e_5_anos_sem_duplicatas():
    base = pd.read_csv(ROOT / "data/siconfi/despesas_oficiais.csv", dtype={"codigo_funcao": str})
    base = validar_oficiais(base)
    assert base.shape[0] == 405
    assert set(base["uf"]) == set(UF_IBGE)
    assert set(base["ano"]) == set(range(2021, 2026))
    a, ausentes = agregar_ufs(base, ano=2025, ufs=list(UF_IBGE), funcoes=list(FUNCOES))
    assert len(a) == 27 and not ausentes


def test_estatisticas_consultam_somente_base_oficial():
    codigo = (ROOT / "pages/4_Estatisticas.py").read_text(encoding="utf-8")
    painel = (ROOT / "utils/dashboard_ui.py").read_text(encoding="utf-8")
    assert "exibir_dashboard()" in codigo
    assert "consultar_dados_oficiais()" in painel
    assert "consultar_status_dados_oficiais()" in painel
    assert "consultar_despesas(" not in codigo
    assert "obter_amostra" not in codigo
    assert "registros_manuais" not in codigo
    assert "Despesas por habitante" not in codigo
