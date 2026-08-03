"""Testes da API HTTP (endpoints e validações)."""
from fastapi.testclient import TestClient

from homepilot.main import app

cliente = TestClient(app)

CONTRATO_BASE = {
    "data_base": "2026-07-17",
    "saldo_devedor": "332786.77",
    "sistema_amortizacao": "price",
    "indexador": "tr",
    "taxa_nominal_anual": "0.1002",
    "taxa_efetiva_informada": "0.1049",
    "prazo_original": 390,
    "prazo_restante": 376,
    "seguros_tarifas_mensais": "130.00",
    "limite_saldo": "350000.00",
    "limite_prestacao": "3800.00",
}

AMORTIZACOES_FGTS = [
    {"data": "2027-06-17", "valor": "40000", "estrategia": "reducao_prazo"},
    {"data": "2029-06-17", "valor": "40000", "estrategia": "reducao_prazo"},
]


def test_health_retorna_status_ok():
    resposta = cliente.get("/api/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_criar_simulacao_com_cenario_inicial():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
        "amortizacoes": AMORTIZACOES_FGTS,
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 200
    corpo_resposta = resposta.json()
    assert len(corpo_resposta["parcelas"]) > 0
    assert corpo_resposta["resumo"]["status_limite_saldo"] in {"Dentro do limite", "Ultrapassado"}


def test_criar_simulacao_pelo_sac():
    corpo = {
        "contrato": {**CONTRATO_BASE, "sistema_amortizacao": "sac"},
        "cenario_tr": {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
        "amortizacoes": AMORTIZACOES_FGTS,
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 200
    parcelas = resposta.json()["parcelas"]
    # marca característica do SAC: a prestação financeira cai do primeiro ao
    # último mês, ao contrário da Price indexada à TR
    assert float(parcelas[-1]["prestacao_financeira"]) < float(parcelas[0]["prestacao_financeira"])


def test_sistema_de_amortizacao_desconhecido_retorna_422():
    corpo = {
        "contrato": {**CONTRATO_BASE, "sistema_amortizacao": "sacre"},
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_criar_simulacao_com_aporte_recorrente():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
        "amortizacoes": [],
        "aportes_recorrentes": [
            {
                "valor": "500.00",
                "periodicidade_meses": 1,
                "mes_inicial": "2026-08-01",
                "mes_final": None,
                "estrategia": "reducao_prazo",
            }
        ],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 200
    corpo_resposta = resposta.json()
    assert len(corpo_resposta["parcelas"]) < 376  # quitou antes do prazo contratado
    assert float(corpo_resposta["resumo"]["total_amortizado_extraordinario"]) > 0


def test_criar_simulacao_com_varios_aportes_recorrentes():
    """R$ 500 por mês em 2026 e R$ 1.500 por mês em 2027."""
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
        "amortizacoes": [],
        "aportes_recorrentes": [
            {
                "valor": "500.00",
                "periodicidade_meses": 1,
                "mes_inicial": "2026-08-01",
                "mes_final": "2026-12-01",
                "estrategia": "reducao_prazo",
            },
            {
                "valor": "1500.00",
                "periodicidade_meses": 1,
                "mes_inicial": "2027-01-01",
                "mes_final": "2027-12-01",
                "estrategia": "reducao_prazo",
            },
        ],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 200
    resumo = resposta.json()["resumo"]
    # 5 meses de R$ 500 + 12 meses de R$ 1.500
    assert float(resumo["total_amortizado_extraordinario"]) == 20500.0


def test_aporte_recorrente_com_periodicidade_zero_retorna_422():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
        "aportes_recorrentes": [
            {
                "valor": "500.00",
                "periodicidade_meses": 0,
                "mes_inicial": "2026-08-01",
                "estrategia": "reducao_prazo",
            }
        ],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_erro_de_recorrente_invalido_diz_qual_deles_corrigir():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
        "aportes_recorrentes": [
            {"valor": "500.00", "periodicidade_meses": 1, "mes_inicial": "2026-08-01"},
            {"valor": "0", "periodicidade_meses": 1, "mes_inicial": "2026-08-01"},
        ],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422
    assert "2º aporte recorrente" in resposta.json()["detail"]


def test_simulacao_sem_aporte_recorrente_continua_valida():
    """O campo é opcional: omitir deve funcionar como antes da recorrência existir."""
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
        "amortizacoes": AMORTIZACOES_FGTS,
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 200


def test_comparar_cenarios_de_tr():
    corpo = {
        "contrato": CONTRATO_BASE,
        "amortizacoes": AMORTIZACOES_FGTS,
        "cenarios": [
            {"nome": "TR 0,0% a.a.", "taxa_anual": "0.0"},
            {"nome": "TR 1,5% a.a.", "taxa_anual": "0.015"},
            {"nome": "TR 2,0% a.a.", "taxa_anual": "0.02"},
            {"nome": "TR 2,5% a.a.", "taxa_anual": "0.025"},
        ],
    }
    resposta = cliente.post("/api/simulations/compare", json=corpo)
    assert resposta.status_code == 200
    resultados = resposta.json()["resultados"]
    assert len(resultados) == 4


def test_saldo_invalido_retorna_422_com_mensagem():
    corpo = {
        "contrato": {**CONTRATO_BASE, "saldo_devedor": "0"},
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422
    assert "saldo" in resposta.json()["detail"].lower()


def test_prazo_zero_retorna_422():
    corpo = {
        "contrato": {**CONTRATO_BASE, "prazo_restante": 0},
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_taxa_negativa_retorna_422():
    corpo = {
        "contrato": {**CONTRATO_BASE, "taxa_nominal_anual": "-0.01"},
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_amortizacao_negativa_retorna_422():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [{"data": "2027-06-17", "valor": "-100", "estrategia": "reducao_prazo"}],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_amortizacao_anterior_a_data_base_retorna_422():
    corpo = {
        "contrato": CONTRATO_BASE,
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [{"data": "2020-01-01", "valor": "1000", "estrategia": "reducao_prazo"}],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422


def test_valores_fora_de_faixa_retorna_422():
    corpo = {
        "contrato": {**CONTRATO_BASE, "saldo_devedor": "999999999999"},
        "cenario_tr": {"nome": "TR", "taxa_anual": "0.015"},
        "amortizacoes": [],
    }
    resposta = cliente.post("/api/simulations", json=corpo)
    assert resposta.status_code == 422
