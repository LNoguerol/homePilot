"""Testes da fórmula da Tabela Price."""
from decimal import Decimal

import pytest

from homepilot.core.tabela_price import calcular_prazo_para_quitar, calcular_prestacao


def test_calcular_prestacao_com_calculo_manual_verificavel():
    """PV=1000, i=1% a.m., n=12 meses -> PMT ≈ 88,85 (calculado manualmente)."""
    prestacao = calcular_prestacao(Decimal("1000"), Decimal("0.01"), 12)
    assert prestacao.quantize(Decimal("0.01")) == Decimal("88.85")


def test_calcular_prestacao_com_taxa_zero_e_divisao_linear():
    prestacao = calcular_prestacao(Decimal("1200"), Decimal("0"), 12)
    assert prestacao == Decimal("100")


def test_calcular_prestacao_prazo_invalido_levanta_erro():
    with pytest.raises(ValueError):
        calcular_prestacao(Decimal("1000"), Decimal("0.01"), 0)


def test_calcular_prazo_para_quitar_e_inverso_da_prestacao():
    """Se calculamos a prestação para (PV, i, n), o prazo recalculado a partir
    dessa prestação deve devolver aproximadamente o mesmo n."""
    pv = Decimal("50000")
    i = Decimal("0.008")
    n = 60
    prestacao = calcular_prestacao(pv, i, n)
    prazo_recalculado = calcular_prazo_para_quitar(pv, i, prestacao)
    assert abs(prazo_recalculado - Decimal(n)) < Decimal("0.01")


def test_calcular_prazo_para_quitar_com_taxa_zero():
    prazo = calcular_prazo_para_quitar(Decimal("1000"), Decimal("0"), Decimal("100"))
    assert prazo == Decimal("10")


def test_calcular_prazo_para_quitar_saldo_zero_retorna_zero_meses():
    prazo = calcular_prazo_para_quitar(Decimal("0"), Decimal("0.01"), Decimal("100"))
    assert prazo == Decimal("0")


def test_calcular_prazo_para_quitar_prestacao_insuficiente_levanta_erro():
    with pytest.raises(ValueError):
        calcular_prazo_para_quitar(Decimal("100000"), Decimal("0.01"), Decimal("50"))
