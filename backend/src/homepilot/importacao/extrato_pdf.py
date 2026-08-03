"""Extração de dados de contrato a partir do bloco de resumo de um extrato bancário em PDF.

Cobre só o cabeçalho do extrato (dados financeiros, taxas, saldo devedor) — a
tabela mensal de parcelas varia demais de layout entre bancos para um parser
genérico valer a pena. Campos não encontrados voltam como `None`; quem chama
decide o que fazer com a lacuna (a API expõe os campos como opcionais e a
tela deixa o usuário completar à mão).
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

    saldo_e_nominal = _PADRAO_SALDO_E_NOMINAL.search(texto)
    if saldo_e_nominal:
        dados.saldo_devedor = _valor_brl_para_decimal(saldo_e_nominal.group(1))
        dados.taxa_nominal_anual = _percentual_para_fracao(saldo_e_nominal.group(2))

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
