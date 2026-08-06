import type {
  AmortizacaoExtraordinaria,
  AporteRecorrente,
  CenarioIndexador,
  CompararSaida,
  ContratoExtraido,
  DadosContrato,
  SimulacaoSaida,
} from "./tipos";

const BASE_URL = "/api";

async function tratarResposta<T>(resposta: Response, mensagemPadrao = "Erro desconhecido."): Promise<T> {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({ detail: mensagemPadrao }));
    // Erros de validação do Pydantic chegam em `detail` como lista de objetos,
    // não como texto — sem esse tratamento a mensagem vira "[object Object]".
    const mensagem =
      typeof corpo.detail === "string"
        ? corpo.detail
        : Array.isArray(corpo.detail)
          ? "Preencha corretamente todos os campos obrigatórios antes de simular."
          : mensagemPadrao;
    throw new Error(mensagem);
  }
  return resposta.json();
}

export async function simular(
  contrato: DadosContrato,
  cenarioIndexador: CenarioIndexador,
  amortizacoes: AmortizacaoExtraordinaria[],
  aportesRecorrentes: AporteRecorrente[],
): Promise<SimulacaoSaida> {
  const resposta = await fetch(`${BASE_URL}/simulations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contrato,
      cenario_indexador: cenarioIndexador,
      amortizacoes,
      aportes_recorrentes: aportesRecorrentes,
    }),
  });
  return tratarResposta<SimulacaoSaida>(resposta, "Erro desconhecido na simulação.");
}

export async function compararCenarios(
  contrato: DadosContrato,
  amortizacoes: AmortizacaoExtraordinaria[],
  cenarios: CenarioIndexador[],
  aportesRecorrentes: AporteRecorrente[],
): Promise<CompararSaida> {
  const resposta = await fetch(`${BASE_URL}/simulations/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contrato, amortizacoes, cenarios, aportes_recorrentes: aportesRecorrentes }),
  });
  return tratarResposta<CompararSaida>(resposta, "Erro desconhecido na comparação.");
}

export async function importarContratoPdf(arquivo: File): Promise<ContratoExtraido> {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  const resposta = await fetch(`${BASE_URL}/contratos/importar-pdf`, {
    method: "POST",
    body: formData,
  });
  return tratarResposta<ContratoExtraido>(resposta, "Não foi possível importar o PDF.");
}
