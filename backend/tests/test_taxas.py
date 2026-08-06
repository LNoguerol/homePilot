"""Testes das conversões de taxas anuais para mensais."""
from decimal import Decimal

from homepilot.core.modelos import Indexador
from homepilot.core.taxas import (
    CENARIOS_PADRAO_POR_INDEXADOR,
    CENARIOS_POUPANCA_PADRAO,
    CENARIOS_TR_PADRAO,
    taxa_anual_para_mensal_equivalente,
    taxa_nominal_anual_para_mensal,
)


def test_taxa_nominal_anual_para_mensal_e_proporcional():
    """12% a.a. nominal -> 1% a.m. (divisão simples por 12)."""
    assert taxa_nominal_anual_para_mensal(Decimal("0.12")) == Decimal("0.01")


def test_taxa_nominal_do_cenario_inicial_bate_com_a_taxa_efetiva_informada():
    """10,02% a.a. nominal deve compor, em 12 meses, para ~10,49% a.a.,
    que é a taxa efetiva informada no contrato do cenário inicial."""
    taxa_mensal = taxa_nominal_anual_para_mensal(Decimal("0.1002"))
    taxa_efetiva_composta = (1 + taxa_mensal) ** 12 - 1
    assert abs(taxa_efetiva_composta - Decimal("0.1049")) < Decimal("0.001")


def test_taxa_anual_para_mensal_equivalente_por_juros_compostos():
    """Fórmula: taxa_mensal = (1 + taxa_anual) ** (1/12) - 1."""
    taxa_mensal = taxa_anual_para_mensal_equivalente(Decimal("0.015"))
    assert abs(taxa_mensal - Decimal("0.0012414877")) < Decimal("0.0000001")


def test_taxa_anual_zero_resulta_em_taxa_mensal_zero():
    assert taxa_anual_para_mensal_equivalente(Decimal("0")) == Decimal("0")


def test_cenarios_tr_padrao_contem_os_quatro_cenarios_iniciais():
    taxas = {taxa for _, taxa in CENARIOS_TR_PADRAO}
    assert taxas == {Decimal("0.0"), Decimal("0.015"), Decimal("0.02"), Decimal("0.025")}


def test_cenarios_poupanca_padrao_contem_os_quatro_cenarios_iniciais():
    taxas = {taxa for _, taxa in CENARIOS_POUPANCA_PADRAO}
    assert taxas == {Decimal("0.05"), Decimal("0.06"), Decimal("0.07"), Decimal("0.08")}


def test_cenarios_padrao_por_indexador_cobre_tr_e_poupanca():
    assert CENARIOS_PADRAO_POR_INDEXADOR[Indexador.TR] == CENARIOS_TR_PADRAO
    assert CENARIOS_PADRAO_POR_INDEXADOR[Indexador.POUPANCA] == CENARIOS_POUPANCA_PADRAO
