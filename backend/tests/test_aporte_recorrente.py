"""Testes dos aportes recorrentes e da soma de aportes na mesma competência."""
from datetime import date
from decimal import Decimal

import pytest

from homepilot.core.excecoes import ErroSimulacaoInvalida
from homepilot.core.modelos import (
    AmortizacaoExtraordinaria,
    AporteRecorrente,
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


def recorrente(**sobrescritas) -> AporteRecorrente:
    valores = dict(
        valor=Decimal("500.00"),
        periodicidade_meses=1,
        mes_inicial=date(2026, 8, 1),
        mes_final=None,
        estrategia=EstrategiaAmortizacao.REDUCAO_PRAZO,
    )
    valores.update(sobrescritas)
    return AporteRecorrente(**valores)


def aporte_em(resultado, ano: int, mes: int) -> Decimal:
    parcela = next(
        p for p in resultado.parcelas if p.competencia.year == ano and p.competencia.month == mes
    )
    return parcela.amortizacao_extraordinaria


def test_aporte_mensal_antecipa_quitacao_e_reduz_juros():
    contrato = contrato_padrao()
    sem = simular(contrato, CENARIO_TR)
    com = simular(contrato, CENARIO_TR, [], [recorrente()])

    assert com.resumo.meses_ate_quitacao < sem.resumo.meses_ate_quitacao
    assert com.resumo.total_juros < sem.resumo.total_juros
    # a economia de juros deve superar com folga o total efetivamente aportado
    economia = sem.resumo.total_juros - com.resumo.total_juros
    assert economia > com.resumo.total_amortizado_extraordinario


def test_aporte_mensal_incide_em_todos_os_meses_ate_quitar():
    resultado = simular(contrato_padrao(), CENARIO_TR, [], [recorrente()])
    # todos os meses recebem aporte, exceto o último (onde o saldo já se esgota
    # na amortização ordinária e não sobra o que amortizar a mais)
    com_aporte = [p for p in resultado.parcelas if p.amortizacao_extraordinaria > 0]
    assert len(com_aporte) >= len(resultado.parcelas) - 1
    assert all(p.amortizacao_extraordinaria == Decimal("500.00") for p in com_aporte)


def test_periodicidade_de_24_meses_reproduz_o_cenario_do_fgts():
    """Aporte a cada 2 anos: mesma coisa que os cinco eventos de FGTS
    cadastrados um a um no cenário inicial do projeto."""
    contrato = contrato_padrao()
    pontuais = [
        AmortizacaoExtraordinaria(date(ano, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
        for ano in (2027, 2029, 2031, 2033, 2035)
    ]
    por_evento = simular(contrato, CENARIO_TR, pontuais)
    por_recorrencia = simular(
        contrato,
        CENARIO_TR,
        [],
        [
            recorrente(
                valor=Decimal("40000"),
                periodicidade_meses=24,
                mes_inicial=date(2027, 6, 1),
                mes_final=date(2035, 6, 30),
            )
        ],
    )

    assert por_recorrencia.resumo.total_amortizado_extraordinario == Decimal("200000.00")
    assert por_recorrencia.resumo.meses_ate_quitacao == por_evento.resumo.meses_ate_quitacao
    assert por_recorrencia.resumo.total_juros == por_evento.resumo.total_juros


def test_recorrentes_em_periodos_distintos_mudam_o_patamar_do_esforco():
    """Caso que motivou a lista: R$ 500 por mês durante 2026 e R$ 1.500 por mês
    durante 2027, cadastrados como duas recorrências sem sobreposição."""
    resultado = simular(
        contrato_padrao(),
        CENARIO_TR,
        [],
        [
            recorrente(valor=Decimal("500"), mes_inicial=date(2026, 8, 1), mes_final=date(2026, 12, 1)),
            recorrente(valor=Decimal("1500"), mes_inicial=date(2027, 1, 1), mes_final=date(2027, 12, 1)),
        ],
    )

    assert aporte_em(resultado, 2026, 8) == Decimal("500.00")
    assert aporte_em(resultado, 2026, 12) == Decimal("500.00")
    assert aporte_em(resultado, 2027, 1) == Decimal("1500.00")
    assert aporte_em(resultado, 2027, 12) == Decimal("1500.00")
    assert aporte_em(resultado, 2028, 1) == Decimal("0.00")
    # 5 meses de R$ 500 + 12 meses de R$ 1.500
    assert resultado.resumo.total_amortizado_extraordinario == Decimal("20500.00")


def test_recorrentes_sobrepostos_somam_na_mesma_competencia():
    """Nada impede sobreposição: um esforço mensal contínuo somado a um reforço
    anual é uma composição legítima, e o mês em que os dois caem recebe a soma."""
    resultado = simular(
        contrato_padrao(),
        CENARIO_TR,
        [],
        [
            recorrente(valor=Decimal("500"), periodicidade_meses=1, mes_inicial=date(2026, 8, 1)),
            recorrente(valor=Decimal("3000"), periodicidade_meses=12, mes_inicial=date(2026, 12, 1)),
        ],
    )

    assert aporte_em(resultado, 2026, 11) == Decimal("500.00")
    assert aporte_em(resultado, 2026, 12) == Decimal("3500.00")
    assert aporte_em(resultado, 2027, 12) == Decimal("3500.00")


def test_recorrente_e_pontual_convivem_com_varios_recorrentes():
    pontual = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    resultado = simular(
        contrato_padrao(),
        CENARIO_TR,
        pontual,
        [
            recorrente(valor=Decimal("500"), periodicidade_meses=1, mes_inicial=date(2026, 8, 1)),
            recorrente(valor=Decimal("200"), periodicidade_meses=6, mes_inicial=date(2026, 12, 1)),
        ],
    )

    # 06/2027: pontual de 40.000 + mensal de 500 + semestral de 200
    assert aporte_em(resultado, 2027, 6) == Decimal("40700.00")


def test_aporte_pontual_e_recorrente_no_mesmo_mes_somam():
    """Regressão da regra antiga: o motor aplicava só o primeiro aporte da
    competência e descartava os demais, o que fazia um aporte recorrente mensal
    engolir silenciosamente todo aporte pontual do contrato."""
    contrato = contrato_padrao()
    pontual = [
        AmortizacaoExtraordinaria(date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRAZO)
    ]
    resultado = simular(contrato, CENARIO_TR, pontual, [recorrente()])

    assert aporte_em(resultado, 2027, 6) == Decimal("40500.00")


def test_dois_aportes_pontuais_na_mesma_competencia_somam():
    contrato = contrato_padrao()
    pontuais = [
        AmortizacaoExtraordinaria(date(2027, 6, 5), Decimal("10000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
        AmortizacaoExtraordinaria(date(2027, 6, 20), Decimal("15000"), EstrategiaAmortizacao.REDUCAO_PRAZO),
    ]
    resultado = simular(contrato, CENARIO_TR, pontuais)

    assert aporte_em(resultado, 2027, 6) == Decimal("25000.00")
    assert resultado.resumo.total_amortizado_extraordinario == Decimal("25000.00")


def test_estrategia_do_aporte_pontual_prevalece_sobre_a_do_recorrente():
    contrato = contrato_padrao()
    pontual = [
        AmortizacaoExtraordinaria(
            date(2027, 6, 17), Decimal("40000"), EstrategiaAmortizacao.REDUCAO_PRESTACAO
        )
    ]
    resultado = simular(
        contrato, CENARIO_TR, pontual, [recorrente(estrategia=EstrategiaAmortizacao.REDUCAO_PRAZO)]
    )

    mes = next(p for p in resultado.parcelas if p.competencia.year == 2027 and p.competencia.month == 6)
    assert mes.estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRESTACAO
    # nos meses só com recorrente, vale a estratégia da recorrência
    outro_mes = next(p for p in resultado.parcelas if p.competencia.year == 2027 and p.competencia.month == 7)
    assert outro_mes.estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRAZO


def test_estrategia_do_primeiro_recorrente_prevalece_entre_recorrentes():
    """Sem pontual no mês, o desempate entre recorrências é a ordem de cadastro —
    a mesma ordem que o usuário vê na tela."""
    resultado = simular(
        contrato_padrao(),
        CENARIO_TR,
        [],
        [
            recorrente(
                valor=Decimal("500"),
                periodicidade_meses=1,
                mes_inicial=date(2026, 8, 1),
                estrategia=EstrategiaAmortizacao.REDUCAO_PRESTACAO,
            ),
            recorrente(
                valor=Decimal("300"),
                periodicidade_meses=1,
                mes_inicial=date(2026, 8, 1),
                estrategia=EstrategiaAmortizacao.REDUCAO_PRAZO,
            ),
        ],
    )

    assert resultado.parcelas[0].amortizacao_extraordinaria == Decimal("800.00")
    assert resultado.parcelas[0].estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRESTACAO


def test_lista_vazia_de_recorrentes_equivale_a_nenhuma_recorrencia():
    contrato = contrato_padrao()
    sem_argumento = simular(contrato, CENARIO_TR)
    com_lista_vazia = simular(contrato, CENARIO_TR, [], [])
    assert com_lista_vazia.resumo == sem_argumento.resumo


def test_mes_final_encerra_a_recorrencia():
    contrato = contrato_padrao()
    resultado = simular(
        contrato,
        CENARIO_TR,
        [],
        [recorrente(mes_inicial=date(2026, 8, 1), mes_final=date(2027, 7, 31))],
    )
    # 12 competências de 08/2026 a 07/2027, R$ 500 cada
    assert resultado.resumo.total_amortizado_extraordinario == Decimal("6000.00")
    assert all(
        p.amortizacao_extraordinaria == 0
        for p in resultado.parcelas
        if (p.competencia.year, p.competencia.month) > (2027, 7)
    )


def test_recorrencia_no_sac_tambem_antecipa_a_quitacao():
    contrato = contrato_padrao(sistema_amortizacao=SistemaAmortizacao.SAC)
    sem = simular(contrato, CENARIO_TR)
    com = simular(contrato, CENARIO_TR, [], [recorrente()])
    assert com.resumo.meses_ate_quitacao < sem.resumo.meses_ate_quitacao
    assert com.parcelas[-1].saldo_final == Decimal("0.00")


def test_valor_recorrente_invalido_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(), CENARIO_TR, [], [recorrente(valor=Decimal("0"))])


def test_periodicidade_invalida_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(), CENARIO_TR, [], [recorrente(periodicidade_meses=0)])


def test_mes_inicial_anterior_a_data_base_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(contrato_padrao(), CENARIO_TR, [], [recorrente(mes_inicial=date(2026, 6, 1))])


def test_mes_final_anterior_ao_inicial_levanta_erro():
    with pytest.raises(ErroSimulacaoInvalida):
        simular(
            contrato_padrao(),
            CENARIO_TR,
            [],
            [recorrente(mes_inicial=date(2027, 6, 1), mes_final=date(2026, 12, 31))],
        )


def test_mensagem_de_erro_identifica_qual_recorrente_esta_invalido():
    """Com várias recorrências na tela, a mensagem precisa dizer qual delas
    corrigir; com uma só, numerar seria ruído."""
    with pytest.raises(ErroSimulacaoInvalida) as erro_com_varias:
        simular(
            contrato_padrao(),
            CENARIO_TR,
            [],
            [recorrente(), recorrente(valor=Decimal("-10"))],
        )
    assert "2º aporte recorrente" in str(erro_com_varias.value)

    with pytest.raises(ErroSimulacaoInvalida) as erro_com_uma:
        simular(contrato_padrao(), CENARIO_TR, [], [recorrente(valor=Decimal("-10"))])
    assert "2º" not in str(erro_com_uma.value)


def test_recorrencia_na_mesma_competencia_da_data_base_e_valida():
    """A data-base é 17/07/2026 e o primeiro mês do cronograma é 08/2026. Iniciar
    a recorrência em 07/2026 não é erro: mensalmente ela já incide no primeiro mês
    simulado."""
    resultado = simular(contrato_padrao(), CENARIO_TR, [], [recorrente(mes_inicial=date(2026, 7, 1))])
    assert resultado.parcelas[0].amortizacao_extraordinaria == Decimal("500.00")


def test_periodicidade_ancora_a_fase_no_mes_inicial():
    """Com periodicidade de 12 meses a partir de 07/2026 — mês que nem chega a ser
    simulado, pois o cronograma começa em 08/2026 —, os aportes caem nos julhos
    seguintes, e não no primeiro mês do cronograma."""
    resultado = simular(
        contrato_padrao(),
        CENARIO_TR,
        [],
        [recorrente(periodicidade_meses=12, mes_inicial=date(2026, 7, 1))],
    )
    meses_com_aporte = {
        (p.competencia.year, p.competencia.month)
        for p in resultado.parcelas
        if p.amortizacao_extraordinaria > 0
    }
    assert (2026, 8) not in meses_com_aporte
    assert (2027, 7) in meses_com_aporte
    assert (2028, 7) in meses_com_aporte
    assert all(mes == 7 for _, mes in meses_com_aporte)
