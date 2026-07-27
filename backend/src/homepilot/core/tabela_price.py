"""Fórmulas da Tabela Price (Sistema Francês de Amortização)."""
from decimal import Decimal

from homepilot.core.excecoes import ErroSimulacaoInvalida

UM = Decimal(1)


def calcular_prestacao(saldo: Decimal, taxa_mensal: Decimal, prazo_meses: int) -> Decimal:
    """Calcula a prestação financeira (PMT) pela fórmula da Tabela Price.

    PMT = PV * [i * (1+i)^n] / [(1+i)^n - 1]

    Onde PV é o saldo financiado, i é a taxa mensal de juros e n é o prazo
    restante em meses. Quando a taxa é zero, a relação se reduz a uma divisão
    linear do saldo pelo prazo.
    """
    if prazo_meses <= 0:
        raise ValueError("prazo_meses deve ser maior que zero para calcular a prestação")
    if taxa_mensal == 0:
        return saldo / Decimal(prazo_meses)
    fator = (UM + taxa_mensal) ** prazo_meses
    return saldo * (taxa_mensal * fator) / (fator - UM)


def calcular_prazo_para_quitar(saldo: Decimal, taxa_mensal: Decimal, prestacao: Decimal) -> Decimal:
    """Calcula, de forma contínua (não arredondada), quantos meses são
    necessários para quitar `saldo`, mantendo a `prestacao` financeira e a
    `taxa_mensal` vigentes constantes.

    Isola n na fórmula da Tabela Price:
        n = -ln(1 - i * PV / PMT) / ln(1 + i)

    Quando a taxa mensal é zero, a relação é linear: n = PV / PMT.
    """
    if saldo <= 0:
        return Decimal(0)
    if taxa_mensal == 0:
        return saldo / prestacao
    razao = UM - (taxa_mensal * saldo / prestacao)
    if razao <= 0:
        raise ErroSimulacaoInvalida(
            "A prestação financeira é insuficiente para pagar os juros do saldo informado."
        )
    return -(razao.ln()) / (UM + taxa_mensal).ln()
