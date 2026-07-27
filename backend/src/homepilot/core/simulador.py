"""Motor de simulação mensal do financiamento.

Implementa a convenção descrita na seção 6 do README do projeto:

1. Obter o saldo inicial do mês.
2. Aplicar a correção monetária pela TR.
3. Calcular os juros do período sobre o saldo já corrigido.
4. Calcular a prestação financeira pela Tabela Price (recalculada a cada mês
   com base no saldo corrigido e no prazo restante vigentes).
5. Calcular a amortização ordinária = prestação financeira - juros.
6. Aplicar a amortização ordinária.
7. Aplicar eventual amortização extraordinária do mês.
8. Recalcular o prazo (redução de prazo) ou a prestação (redução de
   prestação), conforme a estratégia da amortização extraordinária.
9. Somar seguros e tarifas para obter a prestação total.
10. Registrar o saldo final do mês.

Importante: recalcular a prestação financeira todo mês com base no saldo
corrigido pela TR (em vez de mantê-la fixa do início ao fim) é o que permite
que a prestação acompanhe a evolução da TR ao longo do contrato, como ocorre
na prática em financiamentos SFH indexados à TR. Como consequência natural
dessa recorrência, quando resta exatamente 1 mês de prazo a fórmula da Tabela
Price devolve automaticamente o valor exato para zerar o saldo (saldo +
juros), o que resolve o ajuste da última parcela sem necessidade de um caso
especial. Esta é uma simplificação deliberada — não reproduz necessariamente
critérios internos de um banco específico.
"""
from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from homepilot.core.excecoes import ErroSimulacaoInvalida
from homepilot.core.modelos import (
    AmortizacaoExtraordinaria,
    CenarioTR,
    DadosContrato,
    EstrategiaAmortizacao,
    ParcelaMensal,
    ResultadoSimulacao,
)
from homepilot.core.resumos import montar_resumo
from homepilot.core.tabela_price import calcular_prazo_para_quitar, calcular_prestacao
from homepilot.core.taxas import taxa_anual_para_mensal_equivalente, taxa_nominal_anual_para_mensal

CENTAVO = Decimal("0.01")
LIMITE_MESES_SEGURANCA = 720  # trava de segurança contra simulações sem quitação (60 anos)
LIMITE_TAXA_ANUAL_RAZOAVEL = Decimal("1")  # 100% a.a.
LIMITE_SALDO_RAZOAVEL = Decimal("100000000")  # R$ 100 milhões
LIMITE_PRAZO_RAZOAVEL = 600  # meses


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _somar_meses(data_base: date, meses: int) -> date:
    """Soma `meses` a `data_base`, preservando o dia quando possível."""
    mes_total = data_base.month - 1 + meses
    ano = data_base.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(data_base.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def _mesma_competencia(a: date, b: date) -> bool:
    return a.year == b.year and a.month == b.month


def validar_contrato(contrato: DadosContrato) -> None:
    """Valida os dados do contrato, levantando ErroSimulacaoInvalida com
    mensagens compreensíveis para o usuário final."""
    if contrato.saldo_devedor <= 0:
        raise ErroSimulacaoInvalida("O saldo devedor informado é inválido: deve ser maior que zero.")
    if contrato.saldo_devedor > LIMITE_SALDO_RAZOAVEL:
        raise ErroSimulacaoInvalida("O saldo devedor informado está fora de uma faixa razoável.")
    if contrato.prazo_original <= 0:
        raise ErroSimulacaoInvalida("O prazo original deve ser maior que zero.")
    if contrato.prazo_restante <= 0:
        raise ErroSimulacaoInvalida("O prazo restante deve ser maior que zero.")
    if contrato.prazo_restante > LIMITE_PRAZO_RAZOAVEL:
        raise ErroSimulacaoInvalida(
            f"O prazo restante informado está fora de uma faixa razoável (máximo {LIMITE_PRAZO_RAZOAVEL} meses)."
        )
    if contrato.taxa_nominal_anual < 0:
        raise ErroSimulacaoInvalida("A taxa nominal anual não pode ser negativa.")
    if contrato.taxa_efetiva_informada < 0:
        raise ErroSimulacaoInvalida("A taxa efetiva informada não pode ser negativa.")
    if contrato.taxa_nominal_anual > LIMITE_TAXA_ANUAL_RAZOAVEL:
        raise ErroSimulacaoInvalida("A taxa nominal anual informada está fora de uma faixa razoável.")
    if contrato.seguros_tarifas_mensais < 0:
        raise ErroSimulacaoInvalida("O valor de seguros e tarifas não pode ser negativo.")
    if contrato.limite_saldo <= 0 or contrato.limite_prestacao <= 0:
        raise ErroSimulacaoInvalida("Os limites financeiros devem ser maiores que zero.")


def validar_amortizacoes(contrato: DadosContrato, amortizacoes: list[AmortizacaoExtraordinaria]) -> None:
    for amortizacao in amortizacoes:
        if amortizacao.valor <= 0:
            raise ErroSimulacaoInvalida("O valor de uma amortização extraordinária deve ser maior que zero.")
        if amortizacao.data < contrato.data_base:
            raise ErroSimulacaoInvalida(
                "Existe uma amortização extraordinária com data anterior à data-base da simulação."
            )


def validar_taxa_tr(taxa_anual: Decimal) -> None:
    if taxa_anual < 0:
        raise ErroSimulacaoInvalida("A taxa da TR não pode ser negativa.")
    if taxa_anual > LIMITE_TAXA_ANUAL_RAZOAVEL:
        raise ErroSimulacaoInvalida("A taxa da TR informada está fora de uma faixa razoável.")


def simular(
    contrato: DadosContrato,
    cenario_tr: CenarioTR,
    amortizacoes: list[AmortizacaoExtraordinaria] | None = None,
) -> ResultadoSimulacao:
    """Executa a simulação mensal completa do financiamento e devolve o
    cronograma mês a mês junto com o resumo de indicadores."""
    amortizacoes_ordenadas = sorted(amortizacoes or [], key=lambda a: a.data)

    validar_contrato(contrato)
    validar_amortizacoes(contrato, amortizacoes_ordenadas)
    validar_taxa_tr(cenario_tr.taxa_anual)

    taxa_mensal_juros = taxa_nominal_anual_para_mensal(contrato.taxa_nominal_anual)
    taxa_mensal_tr = taxa_anual_para_mensal_equivalente(cenario_tr.taxa_anual)

    saldo = contrato.saldo_devedor
    prazo_restante = contrato.prazo_restante

    prestacao_inicial = calcular_prestacao(saldo, taxa_mensal_juros, prazo_restante)
    if prestacao_inicial <= saldo * taxa_mensal_juros:
        raise ErroSimulacaoInvalida(
            "A prestação financeira calculada é insuficiente para pagar os juros do saldo informado."
        )

    parcelas: list[ParcelaMensal] = []
    amortizacoes_pendentes = list(amortizacoes_ordenadas)

    numero_mes = 0
    while saldo > 0 and prazo_restante > 0:
        numero_mes += 1
        if numero_mes > LIMITE_MESES_SEGURANCA:
            raise ErroSimulacaoInvalida(
                "A simulação ultrapassou o limite de segurança de meses sem atingir a quitação."
            )

        competencia = _somar_meses(contrato.data_base, numero_mes)

        saldo_inicial = saldo
        correcao_tr = _arredondar(saldo_inicial * taxa_mensal_tr)
        saldo_corrigido = saldo_inicial + correcao_tr
        juros = _arredondar(saldo_corrigido * taxa_mensal_juros)

        prestacao_financeira = _arredondar(calcular_prestacao(saldo_corrigido, taxa_mensal_juros, prazo_restante))
        amortizacao_ordinaria = prestacao_financeira - juros
        saldo_apos_ordinaria = saldo_corrigido - amortizacao_ordinaria

        amortizacao_extra = Decimal("0")
        estrategia_aplicada: EstrategiaAmortizacao | None = None

        evento = next(
            (a for a in amortizacoes_pendentes if _mesma_competencia(a.data, competencia)),
            None,
        )

        if evento is not None:
            amortizacoes_pendentes.remove(evento)
            amortizacao_extra = min(evento.valor, saldo_apos_ordinaria)
            estrategia_aplicada = evento.estrategia
            saldo_apos_extra = saldo_apos_ordinaria - amortizacao_extra

            if saldo_apos_extra <= 0:
                prazo_restante = 1
            elif estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRAZO:
                novo_prazo = calcular_prazo_para_quitar(saldo_apos_extra, taxa_mensal_juros, prestacao_financeira)
                prazo_restante = max(1, int(novo_prazo.to_integral_value(rounding=ROUND_CEILING)))
            else:  # REDUCAO_PRESTACAO: mantém o prazo restante, apenas decrementa o mês corrente
                prazo_restante = prazo_restante - 1 if prazo_restante > 1 else 1
        else:
            saldo_apos_extra = saldo_apos_ordinaria
            prazo_restante = prazo_restante - 1 if prazo_restante > 1 else 0

        saldo_final = saldo_apos_extra if saldo_apos_extra > 0 else Decimal("0")
        if saldo_final == 0:
            prazo_restante = 0

        seguros_tarifas = contrato.seguros_tarifas_mensais
        prestacao_total = _arredondar(prestacao_financeira + seguros_tarifas)

        parcelas.append(
            ParcelaMensal(
                numero_mes=numero_mes,
                competencia=competencia,
                saldo_inicial=_arredondar(saldo_inicial),
                correcao_tr=correcao_tr,
                saldo_corrigido=_arredondar(saldo_corrigido),
                juros=juros,
                prestacao_financeira=prestacao_financeira,
                amortizacao_ordinaria=_arredondar(amortizacao_ordinaria),
                amortizacao_extraordinaria=_arredondar(amortizacao_extra),
                seguros_tarifas=_arredondar(seguros_tarifas),
                prestacao_total=prestacao_total,
                saldo_final=_arredondar(saldo_final),
                prazo_restante=prazo_restante,
                estrategia_aplicada=estrategia_aplicada,
                alerta_saldo=saldo_final > contrato.limite_saldo,
                alerta_prestacao=prestacao_total > contrato.limite_prestacao,
            )
        )

        saldo = saldo_final

    resumo = montar_resumo(contrato, parcelas)
    return ResultadoSimulacao(parcelas=parcelas, resumo=resumo)
