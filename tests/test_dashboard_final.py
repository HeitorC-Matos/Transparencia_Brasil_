"""Verificação da consistência e rastreabilidade do dashboard final."""
from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from utils.dashboard_final import chave_recorte, montar_visao
from utils.estatisticas_oficiais import validar_oficiais


def _registro(uf, ano, funcao, valor):
    from services.siconfi import FUNCOES_CODIGO, UF_IBGE
    return {
        "uf": uf, "estado": UF_IBGE[uf][1], "ano": ano, "funcao": funcao,
        "codigo_funcao": FUNCOES_CODIGO[funcao], "valor_reais": valor,
        "periodo": 6, "cod_conta": "RREO2TotalDespesas",
        "fonte_url": "https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/rreo",
    }


def _base_teste():
    return validar_oficiais(pd.DataFrame([
        _registro("SP", 2025, "Educação", 500),
        _registro("SP", 2025, "Saúde", 300),
        _registro("GO", 2025, "Educação", 200),
        _registro("GO", 2025, "Saúde", 100),
        _registro("BA", 2025, "Educação", 70),  # Saúde ausente, não somar parcialmente
        _registro("SP", 2024, "Educação", 450),
        _registro("SP", 2024, "Saúde", 250),
        _registro("GO", 2024, "Educação", 160),
        _registro("GO", 2024, "Saúde", 90),
    ]))


def test_dashboard_descarta_uf_incompleta_sem_substituir_zero():
    painel = montar_visao(_base_teste(), ano=2025, ufs=["SP", "GO", "BA"],
                          funcoes=["Educação", "Saúde"], ufs_historico=["SP", "GO"])
    assert painel.cobertura == 5
    assert painel.combinacoes_esperadas == 6
    assert painel.soma == pytest.approx(1100)
    assert painel.ufs_completas == ["SP", "GO"]
    assert painel.pendencias == [{"uf": "BA", "funcoes_ausentes": ["Saúde"]}]
    assert dict(zip(painel.totais_funcao["funcao"], painel.totais_funcao["valor_reais"])) == {
        "Educação": pytest.approx(700), "Saúde": pytest.approx(400),
    }
    assert len(painel.fontes) == 1
    assert all(uf in {"SP", "GO"} for uf in painel.serie_historica["uf"])


def test_dashboard_filtra_ano_e_funcao_corretamente():
    painel = montar_visao(_base_teste(), ano=2024, ufs=["SP", "GO"], funcoes=["Saúde"])
    assert painel.soma == pytest.approx(340)
    assert painel.cobertura == painel.combinacoes_esperadas == 2
    assert painel.ranking.iloc[0]["uf"] == "SP"
    assert painel.recorte["ano"].eq(2024).all()
    assert painel.recorte["funcao"].eq("Saúde").all()


def test_dashboard_nao_inventa_soma_quando_tudo_incompleto():
    painel = montar_visao(_base_teste(), ano=2025, ufs=["BA"],
                          funcoes=["Educação", "Saúde"])
    assert painel.soma is None
    assert painel.totais_funcao.empty
    assert painel.ranking.empty


def test_dashboard_zero_real_diferente_de_ausente():
    base = validar_oficiais(pd.DataFrame([_registro("SP", 2025, "Saúde", 0)]))
    painel = montar_visao(base, ano=2025, ufs=["SP"], funcoes=["Saúde"])
    assert painel.soma == 0
    assert painel.cobertura == 1


@pytest.mark.parametrize("ufs, funcoes, ano, historico", [
    ([], ["Saúde"], 2025, None),
    (["SP"], [], 2025, None),
    (["SP", "SP"], ["Saúde"], 2025, None),
    (["SP"], ["Saúde", "Saúde"], 2025, None),
    (["XX"], ["Saúde"], 2025, None),
    (["SP"], ["Outra função"], 2025, None),
    (["SP"], ["Saúde"], 2030, None),
    (["SP"], ["Saúde"], 2025, ["GO"]),
])
def test_dashboard_rejeita_recortes_invalidos(ufs, funcoes, ano, historico):
    with pytest.raises(ValueError):
        montar_visao(_base_teste(), ano=ano, ufs=ufs, funcoes=funcoes, ufs_historico=historico)


def test_chave_recorte_canonica_e_dependente_de_filtros():
    assert chave_recorte(2025, ["SP", "GO"], ["Educação", "Saúde"]) == \
           chave_recorte(2025, ["GO", "SP"], ["Saúde", "Educação"])
    assert chave_recorte(2025, ["SP"], ["Saúde"]) != chave_recorte(2024, ["SP"], ["Saúde"])


def test_api_siconfi_alimenta_dashboard_com_dados_reais_do_pacote():
    cliente = TestClient(app)
    resp = cliente.get("/dados-oficiais", params={"ano": 2025, "limite": 1000})
    assert resp.status_code == 200
    assert resp.json()["total"] == 81  # 27 UFs x 3 funções no exercício
    base = validar_oficiais(pd.DataFrame(resp.json()["dados"]))
    painel = montar_visao(base, ano=2025, ufs=sorted(base["uf"].unique().tolist()),
                          funcoes=["Educação", "Saúde", "Segurança Pública"])
    assert len(painel.ufs_completas) == 27
    assert painel.combinacoes_esperadas == painel.cobertura == 81
    assert painel.soma is not None and painel.soma > 0
    assert len(painel.fontes) >= 1


def test_gastos_publicos_concentra_dashboard_e_qwen_app_apenas_apresenta():
    from pathlib import Path
    projeto = Path(__file__).resolve().parents[1]
    app_texto = (projeto / "app.py").read_text(encoding="utf-8")
    ui = (projeto / "utils" / "dashboard_ui.py").read_text(encoding="utf-8")
    pagina = (projeto / "pages/4_Estatisticas.py").read_text(encoding="utf-8")
    assert "exibir_dashboard()" in pagina
    assert "exibir_dashboard()" not in app_texto
    assert "st.bar_chart" not in app_texto and "st.line_chart" not in app_texto
    for nome in ["st.bar_chart", "st.line_chart", "sintetizar_dados_fiscais_ia(",
                 "perguntar_dados_ia(", "Fonte", "Coleta"]:
        assert nome in ui
    assert "obter_amostra" not in ui and "amostra_dados.csv" not in ui
    assert "if gerar:" in ui
    assert "exibir_analises_detalhadas(" in ui
    ia = (projeto / "pages/7_Assistente_IA.py").read_text(encoding="utf-8")
    assert "resumir_documento_ia(" in ia
    assert "Dados oficiais" in app_texto and "Assistente IA" in app_texto
