"""Testes das amortizações extraordinárias (redução de prazo e de prestação)."""
from datetime import date
from decimal import Decimal

from homepilot.core.modelos import (
    AmortizacaoExtraordinaria,
    CenarioIndexador,
    DadosContrato,
    EstrategiaAmortizacao,
    Indexador,
    SistemaAmortizacao,
)
from homepilot.core.simulador import simular

CENARIO_TR = CenarioIndexador("TR 1,5% a.a.", Decimal("0.015"))


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


def test_amortizacao_extraordinaria_reduz_o_saldo_no_mes_do_evento():
    contrato = contrato_padrao()
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    sem_extra = simular(contrato, CENARIO_TR, [])
    com_extra = simular(contrato, CENARIO_TR, amortizacoes)

    parcela_evento = next(p for p in com_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    assert parcela_evento.amortizacao_extraordinaria == Decimal("40000.00")
    assert parcela_evento.estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRAZO

    parcela_equivalente_sem_extra = next(
        p for p in sem_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6
    )
    assert parcela_evento.saldo_final < parcela_equivalente_sem_extra.saldo_final


def test_reducao_de_prazo_mantem_a_prestacao_e_antecipa_a_quitacao():
    contrato = contrato_padrao()
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    sem_extra = simular(contrato, CENARIO_TR, [])
    com_extra = simular(contrato, CENARIO_TR, amortizacoes)

    assert com_extra.resumo.meses_ate_quitacao < sem_extra.resumo.meses_ate_quitacao

    parcela_evento = next(p for p in com_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    parcela_seguinte = com_extra.parcelas[parcela_evento.numero_mes]  # mês seguinte (índice = numero_mes, 0-based)
    # a prestação financeira do mês seguinte ao evento deve permanecer muito
    # próxima da prestação vigente no momento do evento (pequenas variações
    # decorrem apenas da correção mensal pela TR sobre o novo saldo, e não de
    # uma redução deliberada de prestação).
    assert abs(parcela_seguinte.prestacao_financeira - parcela_evento.prestacao_financeira) < Decimal("50.00")


def test_reducao_de_prestacao_mantem_o_prazo_e_reduz_a_prestacao():
    contrato = contrato_padrao()
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRESTACAO)
    ]
    sem_extra = simular(contrato, CENARIO_TR, [])
    com_extra = simular(contrato, CENARIO_TR, amortizacoes)

    parcela_evento = next(p for p in com_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    parcela_seguinte = com_extra.parcelas[parcela_evento.numero_mes]

    # o prazo total não deve encurtar de forma perceptível (mantém-se
    # praticamente igual ao cenário sem amortização extraordinária)
    assert abs(com_extra.resumo.meses_ate_quitacao - sem_extra.resumo.meses_ate_quitacao) <= 1
    # a prestação do mês seguinte ao evento deve cair de forma significativa
    assert parcela_seguinte.prestacao_financeira < parcela_evento.prestacao_financeira - Decimal("100.00")


def test_amortizacao_maior_que_o_saldo_restante_quita_o_financiamento():
    contrato = contrato_padrao(saldo_devedor=Decimal("40000.00"), prazo_restante=24)
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("1000000.00"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    resultado = simular(contrato, CENARIO_TR, amortizacoes)

    assert resultado.parcelas[-1].saldo_final == Decimal("0.00")
    parcela_evento = next(p for p in resultado.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    assert parcela_evento.saldo_final == Decimal("0.00")
    # a amortização extraordinária efetivamente aplicada nunca deve exceder o
    # saldo disponível naquele mês, mesmo que o valor informado seja maior
    assert parcela_evento.amortizacao_extraordinaria <= parcela_evento.saldo_corrigido


def test_reducao_de_prazo_no_sac_mantem_a_amortizacao_e_antecipa_a_quitacao():
    """No SAC, a grandeza preservada na redução de prazo é a amortização mensal
    (e não a prestação, como na Price)."""
    contrato = contrato_padrao(sistema_amortizacao=SistemaAmortizacao.SAC)
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    sem_extra = simular(contrato, CENARIO_TR, [])
    com_extra = simular(contrato, CENARIO_TR, amortizacoes)

    assert com_extra.resumo.meses_ate_quitacao < sem_extra.resumo.meses_ate_quitacao

    parcela_evento = next(p for p in com_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    parcela_seguinte = com_extra.parcelas[parcela_evento.numero_mes]
    assert abs(parcela_seguinte.amortizacao_ordinaria - parcela_evento.amortizacao_ordinaria) < Decimal("5.00")


def test_reducao_de_prestacao_no_sac_mantem_o_prazo_e_reduz_a_prestacao():
    contrato = contrato_padrao(sistema_amortizacao=SistemaAmortizacao.SAC)
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRESTACAO)
    ]
    sem_extra = simular(contrato, CENARIO_TR, [])
    com_extra = simular(contrato, CENARIO_TR, amortizacoes)

    parcela_evento = next(p for p in com_extra.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    parcela_seguinte = com_extra.parcelas[parcela_evento.numero_mes]

    assert abs(com_extra.resumo.meses_ate_quitacao - sem_extra.resumo.meses_ate_quitacao) <= 1
    assert parcela_seguinte.prestacao_financeira < parcela_evento.prestacao_financeira - Decimal("100.00")


def test_amortizacao_maior_que_o_saldo_quita_o_financiamento_no_sac():
    contrato = contrato_padrao(
        sistema_amortizacao=SistemaAmortizacao.SAC,
        saldo_devedor=Decimal("40000.00"),
        prazo_restante=24,
    )
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("1000000.00"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    resultado = simular(contrato, CENARIO_TR, amortizacoes)

    parcela_evento = next(p for p in resultado.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    assert parcela_evento.saldo_final == Decimal("0.00")
    assert resultado.parcelas[-1].saldo_final == Decimal("0.00")


def test_varias_amortizacoes_extraordinarias_no_cenario_inicial_do_fgts():
    contrato = contrato_padrao()
    amortizacoes = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
        AmortizacaoExtraordinaria(date(2029, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
        AmortizacaoExtraordinaria(date(2031, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
        AmortizacaoExtraordinaria(date(2033, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
        AmortizacaoExtraordinaria(date(2035, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
    ]
    resultado = simular(contrato, CENARIO_TR, amortizacoes)

    assert resultado.resumo.total_amortizado_extraordinario == Decimal("200000.00")
    assert resultado.parcelas[-1].saldo_final == Decimal("0.00")
    assert all(p.saldo_final >= 0 for p in resultado.parcelas)
