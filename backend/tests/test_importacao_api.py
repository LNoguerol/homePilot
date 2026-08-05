"""Testes do endpoint de importação de contrato a partir de um PDF."""
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from homepilot.importacao.extrato_pdf import DadosContratoExtraidos
from homepilot.main import app

cliente = TestClient(app)


def test_importar_pdf_invalido_retorna_422():
    resposta = cliente.post(
        "/api/contratos/importar-pdf",
        files={"arquivo": ("extrato.pdf", b"isto nao e um pdf valido", "application/pdf")},
    )
    assert resposta.status_code == 422


def test_importar_pdf_devolve_campos_reconhecidos(monkeypatch):
    dados_falsos = DadosContratoExtraidos(
        data_base=date(2025, 3, 10),
        saldo_devedor=Decimal("200000.00"),
        sistema_amortizacao="sac",
        taxa_nominal_anual=Decimal("0.095"),
        taxa_efetiva_informada=Decimal("0.099"),
        prazo_original=360,
        prazo_restante=336,
    )
    monkeypatch.setattr("homepilot.api.importacao.extrair_de_pdf", lambda conteudo: dados_falsos)

    resposta = cliente.post(
        "/api/contratos/importar-pdf",
        files={"arquivo": ("extrato.pdf", b"conteudo qualquer", "application/pdf")},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["data_base"] == "2025-03-10"
    assert corpo["saldo_devedor"] == "200000.00"
    assert corpo["sistema_amortizacao"] == "sac"
    assert corpo["prazo_original"] == 360
    assert corpo["prazo_restante"] == 336


def test_importar_pdf_sem_campos_reconhecidos_devolve_tudo_none(monkeypatch):
    monkeypatch.setattr(
        "homepilot.api.importacao.extrair_de_pdf",
        lambda conteudo: DadosContratoExtraidos(),
    )

    resposta = cliente.post(
        "/api/contratos/importar-pdf",
        files={"arquivo": ("extrato.pdf", b"conteudo qualquer", "application/pdf")},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert all(valor is None for valor in corpo.values())
