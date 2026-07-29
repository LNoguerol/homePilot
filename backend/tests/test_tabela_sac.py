"""Testes das fórmulas do SAC (Sistema de Amortização Constante)."""
from decimal import Decimal

import pytest

from homepilot.core.tabela_sac import calcular_amortizacao_constante, calcular_prazo_para_quitar


def test_calcular_amortizacao_constante_com_calculo_manual_verificavel():
    """PV=1200, n=12 meses -> A = 100,00 (divisão linear, sem juros embutidos)."""
    amortizacao = calcular_amortizacao_constante(Decimal("1200"), 12)
    assert amortizacao == Decimal("100")


def test_calcular_amortizacao_constante_nao_depende_da_taxa_de_juros():
    """Ao contrário da Price, a amortização do SAC é puramente PV/n — os juros
    entram apenas na composição da prestação, não no cálculo da amortização."""
    amortizacao = calcular_amortizacao_constante(Decimal("332786.77"), 376)
    assert amortizacao.quantize(Decimal("0.01")) == Decimal("885.07")


def test_calcular_amortizacao_constante_prazo_invalido_levanta_erro():
    with pytest.raises(ValueError):
        calcular_amortizacao_constante(Decimal("1000"), 0)


def test_calcular_prazo_para_quitar_e_inverso_da_amortizacao():
    pv = Decimal("50000")
    n = 60
    amortizacao = calcular_amortizacao_constante(pv, n)
    prazo_recalculado = calcular_prazo_para_quitar(pv, amortizacao)
    assert prazo_recalculado == Decimal(n)


def test_calcular_prazo_para_quitar_saldo_zero_retorna_zero_meses():
    prazo = calcular_prazo_para_quitar(Decimal("0"), Decimal("100"))
    assert prazo == Decimal("0")


def test_calcular_prazo_para_quitar_amortizacao_invalida_levanta_erro():
    with pytest.raises(ValueError):
        calcular_prazo_para_quitar(Decimal("1000"), Decimal("0"))
