<script lang="ts">
  import FormularioContrato from "./lib/componentes/FormularioContrato.svelte";
  import AmortizacoesExtras from "./lib/componentes/AmortizacoesExtras.svelte";
  import CartoesResumo from "./lib/componentes/CartoesResumo.svelte";
  import GraficoSaldo from "./lib/componentes/GraficoSaldo.svelte";
  import GraficoPrestacao from "./lib/componentes/GraficoPrestacao.svelte";
  import GraficoComposicao from "./lib/componentes/GraficoComposicao.svelte";
  import TabelaCronograma from "./lib/componentes/TabelaCronograma.svelte";
  import ComparacaoCenarios from "./lib/componentes/ComparacaoCenarios.svelte";
  import { simular, compararCenarios } from "./lib/api";
  import type { AmortizacaoExtraordinaria, DadosContrato, ResumoCenario, SimulacaoSaida } from "./lib/tipos";

  function contratoInicial(): DadosContrato {
    return {
      data_base: "2026-07-17",
      saldo_devedor: "332786.77",
      sistema_amortizacao: "price",
      indexador: "tr",
      taxa_nominal_anual: "0.1002",
      taxa_efetiva_informada: "0.1049",
      prazo_original: 390,
      prazo_restante: 376,
      seguros_tarifas_mensais: "130.00",
      limite_saldo: "350000.00",
      limite_prestacao: "3800.00",
    };
  }

  function amortizacoesIniciais(): AmortizacaoExtraordinaria[] {
    return [2027, 2029, 2031, 2033, 2035].map((ano) => ({
      data: `${ano}-06-17`,
      valor: "40000.00",
      estrategia: "reducao_prazo",
    }));
  }

  let contrato = contratoInicial();
  let amortizacoes = amortizacoesIniciais();
  let cenarioNome = "TR 1,5% a.a.";
  let taxaTrPersonalizada = "0.015";

  const taxasPorCenario: Record<string, string> = {
    "TR 0,0% a.a.": "0.0",
    "TR 1,5% a.a.": "0.015",
    "TR 2,0% a.a.": "0.02",
    "TR 2,5% a.a.": "0.025",
  };

  let resultado: SimulacaoSaida | null = null;
  let comparacao: ResumoCenario[] | null = null;
  let simulando = false;
  let comparando = false;
  let erro: string | null = null;

  function taxaTrAtual(): string {
    return cenarioNome === "Personalizada" ? taxaTrPersonalizada : taxasPorCenario[cenarioNome];
  }

  async function aoSimular() {
    erro = null;
    simulando = true;
    try {
      resultado = await simular(contrato, { nome: cenarioNome, taxa_anual: taxaTrAtual() }, amortizacoes);
    } catch (e) {
      erro = e instanceof Error ? e.message : "Erro desconhecido na simulação.";
      resultado = null;
    } finally {
      simulando = false;
    }
  }

  async function aoComparar() {
    erro = null;
    comparando = true;
    try {
      const cenarios = Object.entries(taxasPorCenario).map(([nome, taxa_anual]) => ({ nome, taxa_anual }));
      const saida = await compararCenarios(contrato, amortizacoes, cenarios);
      comparacao = saida.resultados;
    } catch (e) {
      erro = e instanceof Error ? e.message : "Erro desconhecido na comparação.";
    } finally {
      comparando = false;
    }
  }

  function restaurar() {
    contrato = contratoInicial();
    amortizacoes = amortizacoesIniciais();
    cenarioNome = "TR 1,5% a.a.";
    taxaTrPersonalizada = "0.015";
    resultado = null;
    comparacao = null;
    erro = null;
  }
</script>

<header class="cabecalho-app">
  <h1>HomePilot</h1>
  <p>Planejamento inteligente para financiamento imobiliário</p>
</header>

<main>
  <FormularioContrato bind:contrato bind:cenarioNome bind:taxaTrPersonalizada />
  <AmortizacoesExtras bind:amortizacoes />

  <div class="barra-acoes">
    <button class="primario" on:click={aoSimular} disabled={simulando}>
      {simulando ? "Simulando..." : "Simular"}
    </button>
    <button class="secundario" on:click={restaurar}>Restaurar valores iniciais</button>
  </div>

  {#if erro}
    <p class="erro">{erro}</p>
  {/if}

  {#if resultado}
    <CartoesResumo resumo={resultado.resumo} />
    <GraficoSaldo parcelas={resultado.parcelas} />
    <GraficoPrestacao parcelas={resultado.parcelas} limitePrestacao={contrato.limite_prestacao} />
    <GraficoComposicao parcelas={resultado.parcelas} />
    <TabelaCronograma parcelas={resultado.parcelas} />
  {/if}

  <ComparacaoCenarios resultados={comparacao} executando={comparando} aoComparar={aoComparar} />
</main>

<style>
  .cabecalho-app {
    text-align: center;
    padding: 1.5rem 1rem;
    background: linear-gradient(135deg, #2f6f4f, #244f38);
    color: white;
  }
  .cabecalho-app h1 {
    margin: 0;
    font-size: 1.8rem;
  }
  .cabecalho-app p {
    margin: 0.25rem 0 0 0;
    opacity: 0.9;
  }
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.25rem;
  }
  .barra-acoes {
    display: flex;
    gap: 0.75rem;
    margin: 1rem 0 1.5rem 0;
    flex-wrap: wrap;
  }
  .primario {
    background: var(--cor-destaque);
    color: white;
    border: none;
    padding: 0.55rem 1.4rem;
    border-radius: 6px;
    font-size: 0.95rem;
    cursor: pointer;
  }
  .secundario {
    background: transparent;
    border: 1px solid var(--cor-destaque);
    color: var(--cor-destaque);
    padding: 0.5rem 1.2rem;
    border-radius: 6px;
    cursor: pointer;
  }
  .erro {
    background: #fdeaea;
    color: #a12020;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }
</style>
