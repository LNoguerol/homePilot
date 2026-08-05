"""Testes do parser do cabeçalho de extrato bancário em PDF.

O texto de exemplo abaixo é fictício, reproduzindo só o layout do bloco de
resumo (dados financeiros, taxas, saldo devedor) como o pdfplumber devolve —
não usamos um PDF real de banco aqui para não versionar dados pessoais.
"""
from datetime import date
from decimal import Decimal

from homepilot.importacao.extrato_pdf import extrair_de_texto

TEXTO_EXEMPLO = """Extrato Financeiro CONTRATO 1111111
Data do contrato 01/02/2024
Situação: Ativo
DADOS CADASTRAIS DADOS FINANCEIROS TAXAS SALDO DEVEDOR
Nome Valor Financiamento Indexador Carteira Nominal(a.a) Nominal(a.m) 200.000,00
FULANO DE TAL 210.000,00 TR SFH - 901 9,50% 0,79%
Sistema Amortização CET(a.a) CESH(a.a) Data da liberação Data Emissão
CPF 000.000.000-00 Valor Imóvel
SAC 10,80% 6,00% 01/02/2024 15/03/2025
Endereço do Imóvel 500.000,00
Origem Recursos Efetiva(a.a) Efetiva(a.m) Data Base
RUA EXEMPLO, 100
Prazo 24/360 POUPANCA 9,90% 0,79% 10/03/2025
"""


def test_extrai_sistema_amortizacao():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.sistema_amortizacao == "sac"


def test_extrai_prazo_original_e_restante():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.prazo_original == 360
    assert dados.prazo_restante == 336


def test_extrai_data_base():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.data_base == date(2025, 3, 10)


def test_extrai_saldo_devedor():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.saldo_devedor == Decimal("200000.00")


def test_extrai_taxa_nominal_anual():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.taxa_nominal_anual == Decimal("0.0950")


def test_extrai_taxa_efetiva_informada():
    dados = extrair_de_texto(TEXTO_EXEMPLO)
    assert dados.taxa_efetiva_informada == Decimal("0.0990")


def test_texto_sem_padroes_reconheciveis_retorna_campos_none():
    dados = extrair_de_texto("um texto qualquer sem nenhum padrão conhecido")
    assert dados.data_base is None
    assert dados.saldo_devedor is None
    assert dados.sistema_amortizacao is None
    assert dados.taxa_nominal_anual is None
    assert dados.taxa_efetiva_informada is None
    assert dados.prazo_original is None
    assert dados.prazo_restante is None
