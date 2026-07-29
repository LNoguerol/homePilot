"""Esquemas Pydantic de entrada/saída da API e conversão para o domínio."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from homepilot.core.modelos import (
    AmortizacaoExtraordinaria,
    AporteRecorrente,
    CenarioTR,
    DadosContrato,
    EstrategiaAmortizacao,
    Indexador,
    ParcelaMensal,
    ResultadoSimulacao,
    ResumoSimulacao,
    SistemaAmortizacao,
)

EstrategiaLiteral = Literal["reducao_prazo", "reducao_prestacao"]
SistemaAmortizacaoLiteral = Literal["price", "sac"]


class ContratoEntrada(BaseModel):
    data_base: date
    saldo_devedor: Decimal
    sistema_amortizacao: SistemaAmortizacaoLiteral = "price"
    indexador: Literal["tr"] = "tr"
    taxa_nominal_anual: Decimal
    taxa_efetiva_informada: Decimal
    prazo_original: int
    prazo_restante: int
    seguros_tarifas_mensais: Decimal
    limite_saldo: Decimal
    limite_prestacao: Decimal


class AmortizacaoEntrada(BaseModel):
    data: date
    valor: Decimal
    estrategia: EstrategiaLiteral = "reducao_prazo"


class AporteRecorrenteEntrada(BaseModel):
    """Aporte extraordinário que se repete a cada N meses.

    Alternativa a cadastrar centenas de `AmortizacaoEntrada` para expressar algo
    como "R$ 500 a mais todo mês". `mes_final=None` significa "até quitar".
    """

    valor: Decimal
    periodicidade_meses: int = Field(default=1, ge=1)
    mes_inicial: date
    mes_final: date | None = None
    estrategia: EstrategiaLiteral = "reducao_prazo"


class CenarioTREntrada(BaseModel):
    nome: str
    taxa_anual: Decimal


class SimulacaoEntrada(BaseModel):
    contrato: ContratoEntrada
    cenario_tr: CenarioTREntrada
    amortizacoes: list[AmortizacaoEntrada] = Field(default_factory=list)
    aporte_recorrente: AporteRecorrenteEntrada | None = None


class ParcelaSaida(BaseModel):
    numero_mes: int
    competencia: date
    saldo_inicial: Decimal
    correcao_tr: Decimal
    saldo_corrigido: Decimal
    juros: Decimal
    prestacao_financeira: Decimal
    amortizacao_ordinaria: Decimal
    amortizacao_extraordinaria: Decimal
    seguros_tarifas: Decimal
    prestacao_total: Decimal
    saldo_final: Decimal
    prazo_restante: int
    estrategia_aplicada: EstrategiaLiteral | None
    alerta_saldo: bool
    alerta_prestacao: bool


class ResumoSaida(BaseModel):
    saldo_inicial: Decimal
    maior_saldo_devedor: Decimal
    maior_prestacao_total: Decimal
    data_quitacao: date
    meses_ate_quitacao: int
    meses_antecipados: int
    total_juros: Decimal
    total_correcao_tr: Decimal
    total_seguros_tarifas: Decimal
    total_amortizado_extraordinario: Decimal
    soma_prestacoes: Decimal
    status_limite_saldo: str
    status_limite_prestacao: str


class SimulacaoSaida(BaseModel):
    parcelas: list[ParcelaSaida]
    resumo: ResumoSaida


class CompararEntrada(BaseModel):
    contrato: ContratoEntrada
    amortizacoes: list[AmortizacaoEntrada] = Field(default_factory=list)
    aporte_recorrente: AporteRecorrenteEntrada | None = None
    cenarios: list[CenarioTREntrada]


class ResumoCenario(BaseModel):
    cenario: str
    taxa_anual: Decimal
    resumo: ResumoSaida


class CompararSaida(BaseModel):
    resultados: list[ResumoCenario]


def contrato_para_dominio(entrada: ContratoEntrada) -> DadosContrato:
    return DadosContrato(
        data_base=entrada.data_base,
        saldo_devedor=entrada.saldo_devedor,
        sistema_amortizacao=SistemaAmortizacao(entrada.sistema_amortizacao),
        indexador=Indexador(entrada.indexador),
        taxa_nominal_anual=entrada.taxa_nominal_anual,
        taxa_efetiva_informada=entrada.taxa_efetiva_informada,
        prazo_original=entrada.prazo_original,
        prazo_restante=entrada.prazo_restante,
        seguros_tarifas_mensais=entrada.seguros_tarifas_mensais,
        limite_saldo=entrada.limite_saldo,
        limite_prestacao=entrada.limite_prestacao,
    )


def amortizacao_para_dominio(entrada: AmortizacaoEntrada) -> AmortizacaoExtraordinaria:
    return AmortizacaoExtraordinaria(
        data=entrada.data,
        valor=entrada.valor,
        estrategia=EstrategiaAmortizacao(entrada.estrategia),
    )


def aporte_recorrente_para_dominio(
    entrada: AporteRecorrenteEntrada | None,
) -> AporteRecorrente | None:
    if entrada is None:
        return None
    return AporteRecorrente(
        valor=entrada.valor,
        periodicidade_meses=entrada.periodicidade_meses,
        mes_inicial=entrada.mes_inicial,
        mes_final=entrada.mes_final,
        estrategia=EstrategiaAmortizacao(entrada.estrategia),
    )


def cenario_para_dominio(entrada: CenarioTREntrada) -> CenarioTR:
    return CenarioTR(nome=entrada.nome, taxa_anual=entrada.taxa_anual)


def parcela_para_saida(parcela: ParcelaMensal) -> ParcelaSaida:
    return ParcelaSaida(
        numero_mes=parcela.numero_mes,
        competencia=parcela.competencia,
        saldo_inicial=parcela.saldo_inicial,
        correcao_tr=parcela.correcao_tr,
        saldo_corrigido=parcela.saldo_corrigido,
        juros=parcela.juros,
        prestacao_financeira=parcela.prestacao_financeira,
        amortizacao_ordinaria=parcela.amortizacao_ordinaria,
        amortizacao_extraordinaria=parcela.amortizacao_extraordinaria,
        seguros_tarifas=parcela.seguros_tarifas,
        prestacao_total=parcela.prestacao_total,
        saldo_final=parcela.saldo_final,
        prazo_restante=parcela.prazo_restante,
        estrategia_aplicada=parcela.estrategia_aplicada.value if parcela.estrategia_aplicada else None,
        alerta_saldo=parcela.alerta_saldo,
        alerta_prestacao=parcela.alerta_prestacao,
    )


def resumo_para_saida(resumo: ResumoSimulacao) -> ResumoSaida:
    return ResumoSaida(**resumo.__dict__)


def resultado_para_saida(resultado: ResultadoSimulacao) -> SimulacaoSaida:
    return SimulacaoSaida(
        parcelas=[parcela_para_saida(p) for p in resultado.parcelas],
        resumo=resumo_para_saida(resultado.resumo),
    )
