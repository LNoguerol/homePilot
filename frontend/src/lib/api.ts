import type {
  AmortizacaoExtraordinaria,
  CenarioTR,
  CompararSaida,
  DadosContrato,
  SimulacaoSaida,
} from "./tipos";

const BASE_URL = "/api";

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({ detail: "Erro desconhecido na simulação." }));
    throw new Error(corpo.detail ?? "Erro desconhecido na simulação.");
  }
  return resposta.json();
}

export async function simular(
  contrato: DadosContrato,
  cenarioTr: CenarioTR,
  amortizacoes: AmortizacaoExtraordinaria[],
): Promise<SimulacaoSaida> {
  const resposta = await fetch(`${BASE_URL}/simulations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contrato, cenario_tr: cenarioTr, amortizacoes }),
  });
  return tratarResposta<SimulacaoSaida>(resposta);
}

export async function compararCenarios(
  contrato: DadosContrato,
  amortizacoes: AmortizacaoExtraordinaria[],
  cenarios: CenarioTR[],
): Promise<CompararSaida> {
  const resposta = await fetch(`${BASE_URL}/simulations/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contrato, amortizacoes, cenarios }),
  });
  return tratarResposta<CompararSaida>(resposta);
}
