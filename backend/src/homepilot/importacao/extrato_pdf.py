"""Extração de dados de contrato a partir do bloco de resumo de um extrato bancário em PDF.

Cobre só o cabeçalho do extrato (dados financeiros, taxas, saldo devedor) — a
tabela mensal de parcelas varia demais de layout entre bancos para um parser
genérico valer a pena. Campos não encontrados voltam como `None`; quem chama
decide o que fazer com a lacuna (a API expõe os campos como opcionais e a
tela deixa o usuário completar à mão).

Layouts reconhecidos hoje: extrato do Bradesco e Demonstrativo Descritivo de
Crédito (DDC) do Itaú. Cada um tem seu próprio conjunto de padrões — o de
prazo/taxa efetiva/data-base tenta o formato do Bradesco primeiro e só cai
para o do Itaú se o primeiro não bater (idem para saldo/taxa nominal). O DDC
do Itaú não tem um campo único de "saldo devedor atual" no cabeçalho (só na
tabela mensal, fora do escopo deste parser), então `saldo_devedor` fica
`None` nesse layout.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

import pdfplumber


class ErroLeituraPdf(Exception):
    """Levantado quando o arquivo enviado não pôde ser lido como PDF."""


@dataclass
class DadosContratoExtraidos:
    data_base: date | None = None
    saldo_devedor: Decimal | None = None
    sistema_amortizacao: str | None = None
    taxa_nominal_anual: Decimal | None = None
    taxa_efetiva_informada: Decimal | None = None
    prazo_original: int | None = None
    prazo_restante: int | None = None


_PADRAO_SISTEMA = re.compile(r"\b(PRICE|SAC)\b")

# "Prazo 13/390 POUPANCA 10,49% 0,83% 17/07/2026" — parcela atual, prazo
# total, origem dos recursos, efetiva a.a., efetiva a.m. e data-base sempre
# nessa ordem, na mesma linha do extrato do Bradesco.
_PADRAO_PRAZO_E_EFETIVA = re.compile(
    r"Prazo\s+(\d+)\s*/\s*(\d+)\s+\S+\s+(\d{1,2},\d+)%\s+\d{1,2},\d+%\s+(\d{2}/\d{2}/\d{4})"
)

# O saldo devedor atual fica na mesma linha do rótulo "Nominal(a.m)" (é o
# valor do bloco vizinho "SALDO DEVEDOR"); a taxa nominal a.a. e a.m. ficam
# na linha seguinte, junto dos dados cadastrais.
_PADRAO_SALDO_E_NOMINAL = re.compile(
    r"Nominal\(a\.m\)\s+([\d.,]+)\s*\n[^\n]*?(\d{1,2},\d+)%\s+\d{1,2},\d+%"
)

# Layout alternativo: Demonstrativo Descritivo de Crédito (DDC) do Itaú. Os
# rótulos não têm espaço entre as palavras internas na extração do pdfplumber
# (ex.: "Prazototaloperação 115", "TaxadeJuros(anual) 6,690948000%") — daí o
# `\s*` (em vez de `\s+`) entre as palavras do rótulo, tolerando os dois casos.
# Diferente do Bradesco, não há um único campo de "saldo devedor atual" nem
# "data base" no cabeçalho; usamos a data de emissão do demonstrativo como
# aproximação da data-base (é a data "as of" do prazo remanescente informado).
_PADRAO_PRAZO_TOTAL_ITAU = re.compile(r"Prazo\s*total\s*opera[çc][ãa]o\s+(\d+)")
_PADRAO_PRAZO_REMANESCENTE_ITAU = re.compile(r"Prazo\s*remanescente\s+(\d+)")
_PADRAO_TAXA_NOMINAL_ANUAL_ITAU = re.compile(r"Taxa\s*de\s*Juros\s*\(anual\)\s+(\d{1,2},\d+)%")
_PADRAO_TAXA_EFETIVA_ANUAL_ITAU = re.compile(r"Taxa\s*efetiva\s*\(anual\)\s+(\d{1,2},\d+)%")
_PADRAO_EMISSAO_ITAU = re.compile(r"Emitido\s*em\s*(\d{1,2})\.(\d{1,2})\.(\d{4})")


def _valor_brl_para_decimal(texto: str) -> Decimal | None:
    try:
        return Decimal(texto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _percentual_para_fracao(texto: str) -> Decimal | None:
    valor = _valor_brl_para_decimal(texto)
    return valor / Decimal("100") if valor is not None else None


def _data_br_para_data(texto: str) -> date | None:
    try:
        dia, mes, ano = (int(parte) for parte in texto.split("/"))
        return date(ano, mes, dia)
    except ValueError:
        return None


def extrair_de_texto(texto: str) -> DadosContratoExtraidos:
    dados = DadosContratoExtraidos()

    sistema = _PADRAO_SISTEMA.search(texto)
    if sistema:
        dados.sistema_amortizacao = sistema.group(1).lower()

    prazo_e_efetiva = _PADRAO_PRAZO_E_EFETIVA.search(texto)
    if prazo_e_efetiva:
        parcela_atual = int(prazo_e_efetiva.group(1))
        prazo_total = int(prazo_e_efetiva.group(2))
        dados.prazo_original = prazo_total
        dados.prazo_restante = prazo_total - parcela_atual
        dados.taxa_efetiva_informada = _percentual_para_fracao(prazo_e_efetiva.group(3))
        dados.data_base = _data_br_para_data(prazo_e_efetiva.group(4))
    else:
        prazo_total_itau = _PADRAO_PRAZO_TOTAL_ITAU.search(texto)
        if prazo_total_itau:
            dados.prazo_original = int(prazo_total_itau.group(1))
        prazo_remanescente_itau = _PADRAO_PRAZO_REMANESCENTE_ITAU.search(texto)
        if prazo_remanescente_itau:
            dados.prazo_restante = int(prazo_remanescente_itau.group(1))
        taxa_efetiva_itau = _PADRAO_TAXA_EFETIVA_ANUAL_ITAU.search(texto)
        if taxa_efetiva_itau:
            dados.taxa_efetiva_informada = _percentual_para_fracao(taxa_efetiva_itau.group(1))
        emissao_itau = _PADRAO_EMISSAO_ITAU.search(texto)
        if emissao_itau:
            dia, mes, ano = (int(grupo) for grupo in emissao_itau.groups())
            dados.data_base = date(ano, mes, dia)

    saldo_e_nominal = _PADRAO_SALDO_E_NOMINAL.search(texto)
    if saldo_e_nominal:
        dados.saldo_devedor = _valor_brl_para_decimal(saldo_e_nominal.group(1))
        dados.taxa_nominal_anual = _percentual_para_fracao(saldo_e_nominal.group(2))
    else:
        taxa_nominal_itau = _PADRAO_TAXA_NOMINAL_ANUAL_ITAU.search(texto)
        if taxa_nominal_itau:
            dados.taxa_nominal_anual = _percentual_para_fracao(taxa_nominal_itau.group(1))

    return dados


def extrair_de_pdf(conteudo: bytes) -> DadosContratoExtraidos:
    try:
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            if not pdf.pages:
                raise ErroLeituraPdf("O PDF enviado não contém páginas.")
            texto = pdf.pages[0].extract_text() or ""
    except ErroLeituraPdf:
        raise
    except Exception as exc:
        raise ErroLeituraPdf("Não foi possível ler o arquivo como PDF.") from exc

    return extrair_de_texto(texto)
