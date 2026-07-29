"""Fórmulas do SAC (Sistema de Amortização Constante).

Diferente da Tabela Price, no SAC a **amortização** é o valor constante e a
prestação é decrescente: cada mês amortiza-se sempre a mesma fatia do saldo e
paga-se juros sobre o saldo remanescente (que cai a cada mês). Por isso a
prestação inicial é maior que na Price, mas o total de juros pago é menor.
"""
from decimal import Decimal

UM = Decimal(1)


def calcular_amortizacao_constante(saldo: Decimal, prazo_meses: int) -> Decimal:
    """Calcula a amortização mensal constante do SAC.

    A = PV / n

    Onde PV é o saldo devedor e n é o prazo restante em meses. No HomePilot esta
    fórmula é reaplicada a cada mês sobre o saldo corrigido e o prazo restante
    vigentes (ver `core.simulador`), então a amortização é constante *entre
    eventos* — ela é reajustada quando a TR corrige o saldo ou quando uma
    amortização extraordinária altera o saldo/prazo.
    """
    if prazo_meses <= 0:
        raise ValueError("prazo_meses deve ser maior que zero para calcular a amortização constante")
    return saldo / Decimal(prazo_meses)


def calcular_prazo_para_quitar(saldo: Decimal, amortizacao_constante: Decimal) -> Decimal:
    """Calcula, de forma contínua (não arredondada), quantos meses são
    necessários para quitar `saldo` mantendo a `amortizacao_constante` vigente.

    No SAC a relação é sempre linear, pois a amortização não depende dos juros:
        n = PV / A

    É o equivalente de `tabela_price.calcular_prazo_para_quitar` e, como lá, só
    é usado na estratégia de redução de prazo após uma amortização
    extraordinária. Aqui não existe o risco de prestação insuficiente para
    pagar os juros: a amortização é paga *além* dos juros, nunca descontada
    deles.
    """
    if saldo <= 0:
        return Decimal(0)
    if amortizacao_constante <= 0:
        raise ValueError("amortizacao_constante deve ser maior que zero para calcular o prazo")
    return saldo / amortizacao_constante
