"""Modelos de domínio do motor financeiro do HomePilot.

Estes modelos são simples dataclasses, propositalmente independentes do Pydantic
e do FastAPI, para manter o motor financeiro desacoplado da camada de API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class SistemaAmortizacao(str, Enum):
    """Sistema de amortização utilizado no contrato."""

    PRICE = "price"
    SAC = "sac"


class Indexador(str, Enum):
    """Índice de correção monetária aplicado ao saldo devedor."""

    TR = "tr"
    POUPANCA = "poupanca"


class EstrategiaAmortizacao(str, Enum):
    """Estratégia adotada ao aplicar uma amortização extraordinária."""

    REDUCAO_PRAZO = "reducao_prazo"
    REDUCAO_PRESTACAO = "reducao_prestacao"


@dataclass
class DadosContrato:
    """Parâmetros editáveis do contrato de financiamento."""

    data_base: date
    saldo_devedor: Decimal
    sistema_amortizacao: SistemaAmortizacao
    indexador: Indexador
    taxa_nominal_anual: Decimal
    taxa_efetiva_informada: Decimal
    prazo_original: int
    prazo_restante: int
    seguros_tarifas_mensais: Decimal = Decimal("0")
    limite_saldo: Decimal | None = None
    limite_prestacao: Decimal | None = None


@dataclass
class AmortizacaoExtraordinaria:
    """Um evento pontual de amortização extraordinária (FGTS, 13º, bônus, etc.)."""

    data: date
    valor: Decimal
    estrategia: EstrategiaAmortizacao


@dataclass
class AporteRecorrente:
    """Um aporte extraordinário que se repete a cada N meses.

    Existe para expressar em poucos campos o que exigiria centenas de eventos
    pontuais — o caso típico é "R$ 500 a mais todo mês até quitar". O motor
    expande a recorrência mês a mês durante a simulação; ela nunca é
    materializada como uma lista de `AmortizacaoExtraordinaria`.

    `mes_inicial` e `mes_final` são tratados com granularidade de **competência**
    (ano e mês); o dia é ignorado. `mes_final=None` significa "até quitar".

    A simulação aceita **várias** recorrências ao mesmo tempo, o que permite
    descrever um esforço que muda de patamar ao longo do contrato ("R$ 500 por
    mês em 2026, R$ 1.500 por mês em 2027"). Nada impede que duas se sobreponham
    numa mesma competência: nesse mês os valores somam, como já ocorre entre
    pontuais.
    """

    valor: Decimal
    periodicidade_meses: int
    mes_inicial: date
    mes_final: date | None
    estrategia: EstrategiaAmortizacao


@dataclass
class CenarioIndexador:
    """Um cenário de taxa anual do indexador (TR, poupança etc.) a ser simulado."""

    nome: str
    taxa_anual: Decimal


@dataclass
class ParcelaMensal:
    """Linha do cronograma mensal produzido pela simulação."""

    numero_mes: int
    competencia: date
    saldo_inicial: Decimal
    correcao_indexador: Decimal
    saldo_corrigido: Decimal
    juros: Decimal
    prestacao_financeira: Decimal
    amortizacao_ordinaria: Decimal
    amortizacao_extraordinaria: Decimal
    seguros_tarifas: Decimal
    prestacao_total: Decimal
    saldo_final: Decimal
    prazo_restante: int
    estrategia_aplicada: EstrategiaAmortizacao | None
    alerta_saldo: bool
    alerta_prestacao: bool


@dataclass
class ResumoSimulacao:
    """Indicadores agregados de uma simulação completa."""

    saldo_inicial: Decimal
    maior_saldo_devedor: Decimal
    maior_prestacao_total: Decimal
    data_quitacao: date
    meses_ate_quitacao: int
    meses_antecipados: int
    total_juros: Decimal
    total_correcao_indexador: Decimal
    total_seguros_tarifas: Decimal
    total_amortizado_extraordinario: Decimal
    soma_prestacoes: Decimal
    status_limite_saldo: str
    status_limite_prestacao: str


@dataclass
class ResultadoSimulacao:
    """Resultado completo de uma simulação: cronograma mensal e resumo."""

    parcelas: list[ParcelaMensal]
    resumo: ResumoSimulacao
