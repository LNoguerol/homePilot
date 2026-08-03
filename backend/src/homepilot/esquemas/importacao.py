"""Esquema de saída da importação de dados de contrato a partir de um PDF."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from homepilot.esquemas.simulacao import SistemaAmortizacaoLiteral


class ContratoExtraidoSaida(BaseModel):
    """Campos reconhecidos no extrato — os não encontrados vêm como `None`."""

    data_base: date | None = None
    saldo_devedor: Decimal | None = None
    sistema_amortizacao: SistemaAmortizacaoLiteral | None = None
    taxa_nominal_anual: Decimal | None = None
    taxa_efetiva_informada: Decimal | None = None
    prazo_original: int | None = None
    prazo_restante: int | None = None
