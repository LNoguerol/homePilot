"""Conversões de taxas anuais para taxas mensais equivalentes.

Premissa central (documentada também no README):

A taxa NOMINAL anual do contrato é convertida para taxa mensal por
proporcionalidade simples (divisão por 12). É essa taxa mensal que é usada
na fórmula da Tabela Price. A taxa EFETIVA anual informada no contrato é
apenas um valor de referência para conferência: ela representa o efeito
composto de 12 aplicações da taxa nominal mensal, ou seja,
(1 + taxa_nominal_anual/12) ** 12 - 1. Para o cenário inicial do HomePilot
(taxa nominal 10,02% a.a.), esse cálculo resulta em aproximadamente 10,49%
a.a., que bate com a taxa efetiva informada no contrato — confirmando a
convenção adotada. A taxa efetiva não é usada diretamente em nenhum cálculo
mensal.

Já a TR e a poupança (e qualquer outro indexador de correção monetária) usam
conversão por juros compostos, pois representam um índice de correção que
capitaliza mês a mês: taxa_mensal = (1 + taxa_anual) ** (1/12) - 1.

A poupança é modelada aqui como um cenário de taxa anual constante, na mesma
convenção simplificada usada para a TR — não implementa a regra oficial do
Banco Central (TR + 0,5% a.m. quando a Selic meta é maior que 8,5% a.a., ou
TR + 70% da Selic meta a.m. caso contrário), que depende da Selic vigente mês
a mês e está fora do escopo desta versão. Ver `docs/regras-financeiras.md`.
"""
from decimal import Decimal

from homepilot.core.modelos import Indexador

DOZE = Decimal(12)
UM = Decimal(1)


def taxa_nominal_anual_para_mensal(taxa_nominal_anual: Decimal) -> Decimal:
    """Converte a taxa nominal anual contratual em taxa mensal de juros.

    Convenção adotada: proporcionalidade simples (taxa_nominal_anual / 12).
    """
    return taxa_nominal_anual / DOZE


def taxa_anual_para_mensal_equivalente(taxa_anual: Decimal) -> Decimal:
    """Converte uma taxa anual em taxa mensal equivalente por juros compostos.

    Fórmula: taxa_mensal = (1 + taxa_anual) ** (1/12) - 1

    Utilizada para a TR e, futuramente, para outros indexadores que sigam a
    mesma convenção de capitalização composta.
    """
    if taxa_anual == 0:
        return Decimal(0)
    base = UM + taxa_anual
    expoente = UM / DOZE
    return base**expoente - UM


CENARIOS_TR_PADRAO: tuple[tuple[str, Decimal], ...] = (
    ("TR 0,0% a.a.", Decimal("0.0")),
    ("TR 1,5% a.a.", Decimal("0.015")),
    ("TR 2,0% a.a.", Decimal("0.02")),
    ("TR 2,5% a.a.", Decimal("0.025")),
)

CENARIOS_POUPANCA_PADRAO: tuple[tuple[str, Decimal], ...] = (
    ("Poupança 5,0% a.a.", Decimal("0.05")),
    ("Poupança 6,0% a.a.", Decimal("0.06")),
    ("Poupança 7,0% a.a.", Decimal("0.07")),
    ("Poupança 8,0% a.a.", Decimal("0.08")),
)

CENARIOS_PADRAO_POR_INDEXADOR: dict[Indexador, tuple[tuple[str, Decimal], ...]] = {
    Indexador.TR: CENARIOS_TR_PADRAO,
    Indexador.POUPANCA: CENARIOS_POUPANCA_PADRAO,
}
