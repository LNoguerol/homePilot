"""Endpoints HTTP de simulação de financiamento."""
from fastapi import APIRouter

from homepilot.core.simulador import simular
from homepilot.esquemas.simulacao import (
    CompararEntrada,
    CompararSaida,
    ResumoCenario,
    SimulacaoEntrada,
    SimulacaoSaida,
    amortizacao_para_dominio,
    aporte_recorrente_para_dominio,
    cenario_para_dominio,
    contrato_para_dominio,
    resultado_para_saida,
    resumo_para_saida,
)

roteador = APIRouter(prefix="/api", tags=["simulações"])


@roteador.post("/simulations", response_model=SimulacaoSaida)
async def criar_simulacao(entrada: SimulacaoEntrada) -> SimulacaoSaida:
    contrato = contrato_para_dominio(entrada.contrato)
    cenario = cenario_para_dominio(entrada.cenario_indexador)
    amortizacoes = [amortizacao_para_dominio(a) for a in entrada.amortizacoes]
    recorrentes = [aporte_recorrente_para_dominio(r) for r in entrada.aportes_recorrentes]

    resultado = simular(contrato, cenario, amortizacoes, recorrentes)
    return resultado_para_saida(resultado)


@roteador.post("/simulations/compare", response_model=CompararSaida)
async def comparar_cenarios(entrada: CompararEntrada) -> CompararSaida:
    contrato = contrato_para_dominio(entrada.contrato)
    amortizacoes = [amortizacao_para_dominio(a) for a in entrada.amortizacoes]
    recorrentes = [aporte_recorrente_para_dominio(r) for r in entrada.aportes_recorrentes]

    resultados = []
    for cenario_entrada in entrada.cenarios:
        cenario = cenario_para_dominio(cenario_entrada)
        resultado = simular(contrato, cenario, amortizacoes, recorrentes)
        resultados.append(
            ResumoCenario(
                cenario=cenario_entrada.nome,
                taxa_anual=cenario_entrada.taxa_anual,
                resumo=resumo_para_saida(resultado.resumo),
            )
        )

    return CompararSaida(resultados=resultados)
