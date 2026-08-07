"""Motor de simulação mensal do financiamento.

Implementa a convenção descrita na seção 6 do README do projeto:

1. Obter o saldo inicial do mês.
2. Aplicar a correção monetária pelo indexador (TR, poupança etc.).
3. Calcular os juros do período sobre o saldo já corrigido.
4. Calcular a prestação financeira e a amortização ordinária pelo sistema de
   amortização do contrato (Tabela Price ou SAC), recalculadas a cada mês com
   base no saldo corrigido e no prazo restante vigentes.
5. Aplicar a amortização ordinária.
6. Aplicar eventual amortização extraordinária do mês.
7. Recalcular o prazo (redução de prazo) ou a prestação (redução de
   prestação), conforme a estratégia da amortização extraordinária.
8. Somar seguros e tarifas para obter a prestação total.
9. Registrar o saldo final do mês.

A diferença entre os dois sistemas está concentrada no passo 4 e na forma de
recalcular o prazo no passo 7:

- **Price**: a prestação financeira é a grandeza calculada e a amortização
  ordinária é o resíduo (prestação - juros). Prestação praticamente constante,
  amortização crescente.
- **SAC**: a amortização ordinária é a grandeza calculada (saldo / prazo) e a
  prestação é a soma (amortização + juros). Amortização constante, prestação
  decrescente.

Importante: recalcular esses valores todo mês com base no saldo corrigido pelo
indexador (em vez de mantê-los fixos do início ao fim) é o que permite que a
prestação acompanhe a evolução do indexador ao longo do contrato, como ocorre
na prática em financiamentos SFH indexados à TR ou à poupança. Como
consequência natural dessa recorrência,
quando resta exatamente 1 mês de prazo ambos os sistemas devolvem
automaticamente o valor exato para zerar o saldo (na Price, saldo + juros; no
SAC, saldo / 1 + juros), o que resolve o ajuste da última parcela sem
necessidade de um caso especial. Esta é uma simplificação deliberada — não
reproduz necessariamente critérios internos de um banco específico.
"""
from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from homepilot.core import tabela_price, tabela_sac
from homepilot.core.excecoes import ErroSimulacaoInvalida
from homepilot.core.modelos import (
    AmortizacaoExtraordinaria,
    AporteRecorrente,
    CenarioIndexador,
    DadosContrato,
    EstrategiaAmortizacao,
    ParcelaMensal,
    ResultadoSimulacao,
    SistemaAmortizacao,
)
from homepilot.core.resumos import montar_resumo
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


def _recorrencia_incide_em(recorrente: AporteRecorrente, competencia: date) -> bool:
    """Diz se a recorrência tem aporte na competência informada.

    Comparações em granularidade de ano/mês: o dia de `mes_inicial`/`mes_final`
    é irrelevante, como já ocorre no casamento dos aportes pontuais.
    """
    meses_desde_inicio = (competencia.year - recorrente.mes_inicial.year) * 12 + (
        competencia.month - recorrente.mes_inicial.month
    )
    if meses_desde_inicio < 0 or meses_desde_inicio % recorrente.periodicidade_meses != 0:
        return False
    if recorrente.mes_final is not None:
        if (competencia.year, competencia.month) > (recorrente.mes_final.year, recorrente.mes_final.month):
            return False
    return True


def _aportes_da_competencia(
    competencia: date,
    pendentes: list[AmortizacaoExtraordinaria],
    recorrentes: list[AporteRecorrente],
) -> tuple[Decimal, EstrategiaAmortizacao | None]:
    """Soma todos os aportes que caem na competência e devolve
    `(valor_total, estrategia)`.

    Todos os aportes de um mesmo mês **somam**: pontuais entre si, recorrentes
    entre si e uns com os outros. Antes da recorrência existir, o motor aplicava
    apenas o primeiro aporte da competência e descartava os demais; com um
    aporte recorrente mensal essa regra descartaria silenciosamente todo aporte
    pontual do contrato, o que a tornaria indefensável.

    A estratégia vigente é a do primeiro aporte **pontual** do mês, por ser o
    ato mais deliberado que uma recorrência configurada uma única vez; na
    ausência de pontuais, vale a da primeira recorrência que incide no mês, na
    ordem em que foram cadastradas.

    Consome de `pendentes` os aportes aplicados (a lista é mutada).
    """
    do_mes = [a for a in pendentes if _mesma_competencia(a.data, competencia)]
    if do_mes:
        pendentes[:] = [a for a in pendentes if not _mesma_competencia(a.data, competencia)]

    total = sum((a.valor for a in do_mes), Decimal("0"))
    estrategia = do_mes[0].estrategia if do_mes else None

    for recorrente in recorrentes:
        if not _recorrencia_incide_em(recorrente, competencia):
            continue
        total += recorrente.valor
        if estrategia is None:
            estrategia = recorrente.estrategia

    return total, estrategia


def _calcular_prestacao_e_amortizacao(
    sistema: SistemaAmortizacao,
    saldo_corrigido: Decimal,
    juros: Decimal,
    taxa_mensal_juros: Decimal,
    prazo_restante: int,
) -> tuple[Decimal, Decimal]:
    """Devolve `(prestacao_financeira, amortizacao_ordinaria)` do mês conforme o
    sistema de amortização do contrato.

    A ordem do cálculo se inverte entre os dois sistemas: na Price a prestação é
    calculada e a amortização é o resíduo; no SAC a amortização é calculada e a
    prestação é a soma com os juros.
    """
    if sistema == SistemaAmortizacao.SAC:
        amortizacao_ordinaria = _arredondar(
            tabela_sac.calcular_amortizacao_constante(saldo_corrigido, prazo_restante)
        )
        if amortizacao_ordinaria <= 0:
            # Saldo pequeno demais em relação ao prazo para render um centavo por
            # mês: amortiza o mínimo possível para garantir progresso e quitação.
            amortizacao_ordinaria = CENTAVO
        amortizacao_ordinaria = min(amortizacao_ordinaria, _arredondar(saldo_corrigido))
        return _arredondar(amortizacao_ordinaria + juros), amortizacao_ordinaria

    prestacao_financeira = _arredondar(
        tabela_price.calcular_prestacao(saldo_corrigido, taxa_mensal_juros, prazo_restante)
    )
    return prestacao_financeira, prestacao_financeira - juros


def _calcular_prazo_apos_reducao(
    sistema: SistemaAmortizacao,
    saldo: Decimal,
    taxa_mensal_juros: Decimal,
    prestacao_financeira: Decimal,
    amortizacao_ordinaria: Decimal,
) -> int:
    """Recalcula o prazo restante na estratégia de redução de prazo, mantendo
    constante a grandeza característica do sistema: a prestação financeira na
    Price, a amortização mensal no SAC."""
    if sistema == SistemaAmortizacao.SAC:
        prazo = tabela_sac.calcular_prazo_para_quitar(saldo, amortizacao_ordinaria)
    else:
        prazo = tabela_price.calcular_prazo_para_quitar(saldo, taxa_mensal_juros, prestacao_financeira)
    return max(1, int(prazo.to_integral_value(rounding=ROUND_CEILING)))


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
    if contrato.limite_saldo is not None and contrato.limite_saldo <= 0:
        raise ErroSimulacaoInvalida("O limite do saldo devedor deve ser maior que zero.")
    if contrato.limite_prestacao is not None and contrato.limite_prestacao <= 0:
        raise ErroSimulacaoInvalida("O limite da prestação total deve ser maior que zero.")


def validar_amortizacoes(contrato: DadosContrato, amortizacoes: list[AmortizacaoExtraordinaria]) -> None:
    for amortizacao in amortizacoes:
        if amortizacao.valor <= 0:
            raise ErroSimulacaoInvalida("O valor de uma amortização extraordinária deve ser maior que zero.")
        if amortizacao.data < contrato.data_base:
            raise ErroSimulacaoInvalida(
                "Existe uma amortização extraordinária com data anterior à data-base da simulação."
            )


def _identificar_recorrente(posicao: int, total: int) -> str:
    """Nomeia a recorrência nas mensagens de erro. Com uma só cadastrada, numerar
    seria ruído; com várias, o número é a única forma de o usuário saber qual das
    linhas da tela precisa corrigir."""
    return "o aporte recorrente" if total == 1 else f"o {posicao}º aporte recorrente"


def validar_aportes_recorrentes(contrato: DadosContrato, recorrentes: list[AporteRecorrente]) -> None:
    total = len(recorrentes)
    for posicao, recorrente in enumerate(recorrentes, start=1):
        qual = _identificar_recorrente(posicao, total)
        if recorrente.valor <= 0:
            raise ErroSimulacaoInvalida(f"O valor d{qual} deve ser maior que zero.")
        if recorrente.periodicidade_meses < 1:
            raise ErroSimulacaoInvalida(f"A periodicidade d{qual} deve ser de pelo menos 1 mês.")
        if recorrente.periodicidade_meses > LIMITE_PRAZO_RAZOAVEL:
            raise ErroSimulacaoInvalida(f"A periodicidade d{qual} está fora de uma faixa razoável.")
        inicio = (recorrente.mes_inicial.year, recorrente.mes_inicial.month)
        if inicio < (contrato.data_base.year, contrato.data_base.month):
            raise ErroSimulacaoInvalida(
                f"O mês inicial d{qual} é anterior à competência da data-base da simulação."
            )
        if recorrente.mes_final is not None:
            fim = (recorrente.mes_final.year, recorrente.mes_final.month)
            if fim < inicio:
                raise ErroSimulacaoInvalida(f"O mês final d{qual} é anterior ao seu mês inicial.")


def validar_taxa_indexador(taxa_anual: Decimal) -> None:
    if taxa_anual < 0:
        raise ErroSimulacaoInvalida("A taxa do indexador não pode ser negativa.")
    if taxa_anual > LIMITE_TAXA_ANUAL_RAZOAVEL:
        raise ErroSimulacaoInvalida("A taxa do indexador informada está fora de uma faixa razoável.")


def simular(
    contrato: DadosContrato,
    cenario_indexador: CenarioIndexador,
    amortizacoes: list[AmortizacaoExtraordinaria] | None = None,
    aportes_recorrentes: list[AporteRecorrente] | None = None,
) -> ResultadoSimulacao:
    """Executa a simulação mensal completa do financiamento e devolve o
    cronograma mês a mês junto com o resumo de indicadores.

    `amortizacoes` são os aportes pontuais; `aportes_recorrentes` são os aportes
    que se repetem a cada N meses e são expandidos durante o laço. Todos
    convivem: num mês em que mais de um incide, os valores somam.
    """
    amortizacoes_ordenadas = sorted(amortizacoes or [], key=lambda a: a.data)
    recorrentes = list(aportes_recorrentes or [])

    validar_contrato(contrato)
    validar_amortizacoes(contrato, amortizacoes_ordenadas)
    validar_aportes_recorrentes(contrato, recorrentes)
    validar_taxa_indexador(cenario_indexador.taxa_anual)

    taxa_mensal_juros = taxa_nominal_anual_para_mensal(contrato.taxa_nominal_anual)
    taxa_mensal_indexador = taxa_anual_para_mensal_equivalente(cenario_indexador.taxa_anual)

    saldo = contrato.saldo_devedor
    prazo_restante = contrato.prazo_restante

    # Checagem só necessária na Price, onde a amortização é o resíduo da
    # prestação: no SAC a amortização é somada aos juros, então a prestação é
    # sempre suficiente por construção.
    if contrato.sistema_amortizacao == SistemaAmortizacao.PRICE:
        prestacao_inicial = tabela_price.calcular_prestacao(saldo, taxa_mensal_juros, prazo_restante)
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
        correcao_indexador = _arredondar(saldo_inicial * taxa_mensal_indexador)
        saldo_corrigido = saldo_inicial + correcao_indexador
        juros = _arredondar(saldo_corrigido * taxa_mensal_juros)

        prestacao_financeira, amortizacao_ordinaria = _calcular_prestacao_e_amortizacao(
            contrato.sistema_amortizacao,
            saldo_corrigido,
            juros,
            taxa_mensal_juros,
            prazo_restante,
        )
        saldo_apos_ordinaria = saldo_corrigido - amortizacao_ordinaria

        estrategia_aplicada: EstrategiaAmortizacao | None = None

        valor_aportes, estrategia_do_mes = _aportes_da_competencia(
            competencia, amortizacoes_pendentes, recorrentes
        )
        # limitado ao saldo disponível: um aporte nunca deixa o saldo negativo
        amortizacao_extra = min(valor_aportes, saldo_apos_ordinaria) if valor_aportes > 0 else Decimal("0")

        if amortizacao_extra > 0:
            estrategia_aplicada = estrategia_do_mes
            saldo_apos_extra = saldo_apos_ordinaria - amortizacao_extra

            if saldo_apos_extra <= 0:
                prazo_restante = 1
            elif estrategia_aplicada == EstrategiaAmortizacao.REDUCAO_PRAZO:
                prazo_restante = _calcular_prazo_apos_reducao(
                    contrato.sistema_amortizacao,
                    saldo_apos_extra,
                    taxa_mensal_juros,
                    prestacao_financeira,
                    amortizacao_ordinaria,
                )
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
                correcao_indexador=correcao_indexador,
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
                alerta_saldo=contrato.limite_saldo is not None and saldo_final > contrato.limite_saldo,
                alerta_prestacao=contrato.limite_prestacao is not None and prestacao_total > contrato.limite_prestacao,
            )
        )

        saldo = saldo_final

    resumo = montar_resumo(contrato, parcelas)
    return ResultadoSimulacao(parcelas=parcelas, resumo=resumo)
