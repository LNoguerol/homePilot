"""Testes do motor de simulação mensal (core.simulador)."""
from datetime import date
from decimal import Decimal

import pytest

from homepilot.core.excecoes import ErroSimulacaoInvalida
from homepilot.core.modelos import (
    CenarioTR,
    DadosContrato,
    Indexador,
    SistemaAmortizacao,
)
from homepilot.core.simulador import simular


def contrato_padrao(**sobrescritas) -> DadosContrato:
    valores = dict(
        data_base=date(2026, 7, 17),
        saldo_devedor=Decimal("332786.77"),
        sistema_amortizacao=SistemaAmortizacao.PRICE,
        indexador=Indexador.TR,
        taxa_nominal_anual=Decimal("0.1002"),
        taxa_efetiva_informada=Decimal("0.1049"),
        prazo_original=390,
        prazo_restante=376,
        seguros_tarifas_mensais=Decimal("130.00"),
        limite_saldo=Decimal("350000.00"),
        limite_prestacao=Decimal("3800.00"),
    )
    valores.update(sobrescritas)
    return DadosContrato(**valores)


def test_saldo_nunca_fica_negativo():
    resultado = simular(contrato_padrao(), CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    assert all(p.saldo_final >= 0 for p in resultado.parcelas)


def test_ajuste_da_ultima_parcela_zera_o_saldo_exatamente():
    resultado = simular(contrato_padrao(), CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    ultima = resultado.parcelas[-1]
    assert ultima.saldo_final == Decimal("0.00")
    assert ultima.prazo_restante == 0


def test_alerta_de_saldo_dispara_ao_ultrapassar_o_limite():
    contrato = contrato_padrao(limite_saldo=Decimal("1000.00"))
    resultado = simular(contrato, CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    assert any(p.alerta_saldo for p in resultado.parcelas)
    assert resultado.resumo.status_limite_saldo == "Ultrapassado"


def test_sem_alerta_de_saldo_quando_dentro_do_limite_configurado():
    """Contrato curto e com limite generoso: o saldo nunca deve ultrapassar."""
    contrato = contrato_padrao(
        saldo_devedor=Decimal("50000.00"),
        prazo_original=24,
        prazo_restante=24,
        limite_saldo=Decimal("200000.00"),
    )
    resultado = simular(contrato, CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    assert not any(p.alerta_saldo for p in resultado.parcelas)
    assert resultado.resumo.status_limite_saldo == "Dentro do limite"


def test_alerta_de_prestacao_dispara_ao_ultrapassar_o_limite():
    contrato = contrato_padrao(limite_prestacao=Decimal("500.00"))
    resultado = simular(contrato, CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    assert any(p.alerta_prestacao for p in resultado.parcelas)
    assert resultado.resumo.status_limite_prestacao == "Ultrapassado"


def test_sem_alerta_de_prestacao_quando_dentro_do_limite_configurado():
    """Contrato curto e com limite generoso: a prestação nunca deve ultrapassar."""
    contrato = contrato_padrao(
        saldo_devedor=Decimal("50000.00"),
        prazo_original=24,
        prazo_restante=24,
        limite_prestacao=Decimal("5000.00"),
    )
    resultado = simular(contrato, CenarioTR("TR 1,5% a.a.", Decimal("0.015")))
    assert not any(p.alerta_prestacao for p in resultado.parcelas)
    assert resultado.resumo.status_limite_prestacao == "Dentro do limite"


def test_comparacao_de_cenarios_de_tr_gera_resultados_diferentes():
    contrato = contrato_padrao()
    resultado_0 = simular(contrato, CenarioTR("TR 0,0% a.a.", Decimal("0.0")))
    resultado_2_5 = simular(contrato, CenarioTR("TR 2,5% a.a.", Decimal("0.025")))

    assert resultado_0.resumo.total_correcao_tr == Decimal("0.00")
    assert resultado_2_5.resumo.total_correcao_tr > resultado_0.resumo.total_correcao_tr
    assert resultado_2_5.resumo.maior_saldo_devedor > resultado_0.resumo.maior_saldo_devedor


def test_saldo_invalido_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(saldo_devedor=Decimal("0")), CenarioTR("TR", Decimal("0.015")))


def test_prazo_menor_ou_igual_a_zero_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(prazo_restante=0), CenarioTR("TR", Decimal("0.015")))


def test_taxa_negativa_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(taxa_nominal_anual=Decimal("-0.01")), CenarioTR("TR", Decimal("0.015")))


def test_taxa_tr_negativa_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(), CenarioTR("TR negativa", Decimal("-0.01")))


def test_valores_fora_de_faixa_razoavel_levantam_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(saldo_devedor=Decimal("999999999999")), CenarioTR("TR", Decimal("0.015")))
