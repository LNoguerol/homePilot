"""Construção do resumo agregado da simulação a partir do cronograma mensal."""
from __future__ import annotations

from decimal import Decimal

from homepilot.core.modelos import DadosContrato, ParcelaMensal, ResumoSimulacao

ZERO = Decimal("0")


def montar_resumo(contrato: DadosContrato, parcelas: list[ParcelaMensal]) -> ResumoSimulacao:
    """Monta o resumo de indicadores a partir do cronograma mensal já calculado."""
    if not parcelas:
        raise ValueError("não é possível montar um resumo sem parcelas simuladas")

    ultima_parcela = parcelas[-1]

    maior_saldo_devedor = max(p.saldo_final for p in parcelas)
    maior_prestacao_total = max(p.prestacao_total for p in parcelas)
    total_juros = sum((p.juros for p in parcelas), ZERO)
    total_correcao_indexador = sum((p.correcao_indexador for p in parcelas), ZERO)
    total_seguros_tarifas = sum((p.seguros_tarifas for p in parcelas), ZERO)
    total_amortizado_extraordinario = sum((p.amortizacao_extraordinaria for p in parcelas), ZERO)
    soma_prestacoes = sum((p.prestacao_total for p in parcelas), ZERO)

    meses_ate_quitacao = ultima_parcela.numero_mes
    meses_antecipados = max(0, contrato.prazo_restante - meses_ate_quitacao)

    status_limite_saldo = "Ultrapassado" if any(p.alerta_saldo for p in parcelas) else "Dentro do limite"
    status_limite_prestacao = "Ultrapassado" if any(p.alerta_prestacao for p in parcelas) else "Dentro do limite"

    return ResumoSimulacao(
        saldo_inicial=contrato.saldo_devedor,
        maior_saldo_devedor=maior_saldo_devedor,
        maior_prestacao_total=maior_prestacao_total,
        data_quitacao=ultima_parcela.competencia,
        meses_ate_quitacao=meses_ate_quitacao,
        meses_antecipados=meses_antecipados,
        total_juros=total_juros,
        total_correcao_indexador=total_correcao_indexador,
        total_seguros_tarifas=total_seguros_tarifas,
        total_amortizado_extraordinario=total_amortizado_extraordinario,
        soma_prestacoes=soma_prestacoes,
        status_limite_saldo=status_limite_saldo,
        status_limite_prestacao=status_limite_prestacao,
    )
