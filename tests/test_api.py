from fastapi.testclient import TestClient
from api.main import app

cliente = TestClient(app)


def test_health():
    assert cliente.get("/health").json() == {"status": "ok"}


def test_get_listagem_e_filtros(dados_isolados):
    resposta = cliente.get("/despesas")
    assert resposta.status_code == 200
    resultado = resposta.json()
    assert resultado["total"] == 9
    assert all(r["origem"] == "amostra_academica" for r in resultado["dados"])
    filtrado = cliente.get("/despesas", params={"sigla": "SP", "funcao": "Saúde", "ano": 2025})
    assert filtrado.json()["total"] == 1
    assert filtrado.json()["dados"][0]["valor_despesa"] == 28500000000
    assert cliente.get("/despesas", params={"limite": 2, "deslocamento": 2}).json()["dados"].__len__() == 2


def test_post_nao_altera_amostra(dados_isolados):
    original = (dados_isolados / "amostra_dados.csv").read_bytes()
    payload = {"sigla": "GO", "ano": 2025, "funcao": "Educação",
               "valor_despesa": 1500.75, "populacao": 7350000}
    resposta = cliente.post("/despesas", json=payload)
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["origem"] == "manual"
    assert corpo["estado"] == "Goiás"
    assert corpo["fonte_fiscal"] == "Cadastro manual — não verificado"
    assert (dados_isolados / "amostra_dados.csv").read_bytes() == original
    assert cliente.get("/despesas", params={"origem": "manual"}).json()["total"] == 1
    assert cliente.get("/despesas", params={"origem": "amostra_academica"}).json()["total"] == 9
    assert cliente.get("/despesas").json()["total"] == 10


def test_post_invalido_nao_persiste(dados_isolados):
    resposta = cliente.post("/despesas", json={
        "sigla": "RJ", "ano": 2025, "funcao": "Educação",
        "valor_despesa": -10, "populacao": 0,
    })
    assert resposta.status_code == 422
    assert not (dados_isolados / "registros_manuais.csv").exists()


def test_estatisticas_e_textos(dados_isolados):
    stats = cliente.get("/estatisticas")
    assert stats.status_code == 200
    assert stats.json()["quantidade"] == 9
    assert stats.json()["total_valor_despesa"] > 0
    web = cliente.get("/conteudo-web")
    assert web.status_code == 200
    assert len(web.json()) == 3
    assert "url" in web.json()[0]
