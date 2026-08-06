<script lang="ts">
  import { onMount } from "svelte";
  import FormularioContrato from "./lib/componentes/FormularioContrato.svelte";
  import AmortizacoesExtras from "./lib/componentes/AmortizacoesExtras.svelte";
  import CartoesResumo from "./lib/componentes/CartoesResumo.svelte";
  import GraficoSaldo from "./lib/componentes/GraficoSaldo.svelte";
  import GraficoPrestacao from "./lib/componentes/GraficoPrestacao.svelte";
  import GraficoComposicao from "./lib/componentes/GraficoComposicao.svelte";
  import TabelaCronograma from "./lib/componentes/TabelaCronograma.svelte";
  import ComparacaoCenarios from "./lib/componentes/ComparacaoCenarios.svelte";
  import TelaLogin from "./lib/componentes/TelaLogin.svelte";
  import TelaCadastro from "./lib/componentes/TelaCadastro.svelte";
  import Logo from "./lib/componentes/Logo.svelte";
  import { simular, compararCenarios } from "./lib/api";
  import { buscarUsuarioAtual, limparToken, obterToken } from "./lib/autenticacao";
  import { CENARIOS_POR_INDEXADOR, ROTULO_INDEXADOR } from "./lib/cenariosIndexador";
  import type {
    AmortizacaoExtraordinaria,
    AporteRecorrente,
    DadosContrato,
    ResumoCenario,
    SimulacaoSaida,
    Usuario,
  } from "./lib/tipos";

  let usuario: Usuario | null = null;
  let verificandoSessao = true;
  let telaAuth: "login" | "cadastro" = "login";

  onMount(async () => {
    if (obterToken()) {
      try {
        usuario = await buscarUsuarioAtual();
      } catch {
        limparToken();
      }
    }
    verificandoSessao = false;
  });

  async function aoAutenticar() {
    usuario = await buscarUsuarioAtual();
  }

  function sair() {
    limparToken();
    usuario = null;
  }

  function contratoInicial(): DadosContrato {
    return {
      data_base: "",
      saldo_devedor: "",
      sistema_amortizacao: "price",
      indexador: "tr",
      taxa_nominal_anual: "",
      taxa_efetiva_informada: "",
      prazo_original: 0,
      prazo_restante: 0,
      seguros_tarifas_mensais: "",
      limite_saldo: "",
      limite_prestacao: "",
    };
  }

  function amortizacoesIniciais(): AmortizacaoExtraordinaria[] {
    return [];
  }

  let contrato = contratoInicial();
  let amortizacoes = amortizacoesIniciais();
  let aportesRecorrentes: AporteRecorrente[] = [];
  let cenarioNome = CENARIOS_POR_INDEXADOR.tr[0].nome;
  let taxaIndexadorPersonalizada = "";

  $: taxasPorCenario = Object.fromEntries(
    CENARIOS_POR_INDEXADOR[contrato.indexador].map((c) => [c.nome, c.taxa]),
  ) as Record<string, string>;

  let resultado: SimulacaoSaida | null = null;
  let resultadoSemAmortizacao: SimulacaoSaida | null = null;
  let comparacao: ResumoCenario[] | null = null;
  let simulando = false;
  let comparando = false;
  let erro: string | null = null;

  const rotulosContrato: Record<keyof DadosContrato, string> = {
    data_base: "Data-base",
    saldo_devedor: "Saldo devedor",
    sistema_amortizacao: "Sistema de amortização",
    indexador: "Indexador",
    taxa_nominal_anual: "Taxa nominal anual",
    taxa_efetiva_informada: "Taxa efetiva informada",
    prazo_original: "Prazo original",
    prazo_restante: "Prazo restante",
    seguros_tarifas_mensais: "Seguros e tarifas mensais",
    limite_saldo: "Limite do saldo devedor",
    limite_prestacao: "Limite da prestação total",
  };

  function taxaIndexadorAtual(): string {
    return cenarioNome === "Personalizada" ? taxaIndexadorPersonalizada : taxasPorCenario[cenarioNome];
  }

  function campoPreenchido(valor: unknown): boolean {
    return valor !== "" && valor !== null && valor !== undefined;
  }

  function camposContratoFaltando(dadosContrato: DadosContrato): (keyof DadosContrato)[] {
    return (Object.keys(rotulosContrato) as (keyof DadosContrato)[])
      .filter((campo) => campo !== "sistema_amortizacao" && campo !== "indexador")
      .filter((campo) => !campoPreenchido(dadosContrato[campo]));
  }

  // Só marca campos em vermelho depois da primeira tentativa de simular —
  // mostrar tudo vermelho num formulário recém-aberto seria pior, não melhor.
  // `contrato` precisa aparecer aqui (e não só dentro da função chamada) para
  // o Svelte rastrear a dependência e recalcular a cada tecla digitada.
  let tentouSimular = false;
  $: camposFaltando = tentouSimular ? new Set(camposContratoFaltando(contrato)) : new Set<keyof DadosContrato>();
  $: indexadorPersonalizadaFaltando =
    tentouSimular && cenarioNome === "Personalizada" && !campoPreenchido(taxaIndexadorPersonalizada);

  /** Campos em branco chegam ao backend como "" e viram um erro 422 críptico
   * do Pydantic — melhor barrar aqui e dizer exatamente o que falta. */
  function validarContrato(): string | null {
    const faltando = camposContratoFaltando(contrato).map((campo) => rotulosContrato[campo]);

    if (cenarioNome === "Personalizada" && !campoPreenchido(taxaIndexadorPersonalizada)) {
      faltando.push(`${ROTULO_INDEXADOR[contrato.indexador]} personalizada`);
    }

    if (faltando.length === 0) return null;
    return `Preencha os campos obrigatórios antes de simular: ${faltando.join(", ")}.`;
  }

  async function aoSimular() {
    erro = null;
    tentouSimular = true;
    const mensagemValidacao = validarContrato();
    if (mensagemValidacao) {
      erro = mensagemValidacao;
      return;
    }
    simulando = true;
    try {
      const temAporteExtra = amortizacoes.length > 0 || aportesRecorrentes.length > 0;
      const cenarioIndexador = { nome: cenarioNome, taxa_anual: taxaIndexadorAtual() };
      const [saidaComAmortizacao, saidaSemAmortizacao] = await Promise.all([
        simular(contrato, cenarioIndexador, amortizacoes, aportesRecorrentes),
        // Linha comparativa do gráfico de saldo: mesmo contrato, sem aportes
        // extraordinários. Só faz sentido buscar quando há aporte a comparar.
        temAporteExtra ? simular(contrato, cenarioIndexador, [], []) : Promise.resolve(null),
      ]);
      resultado = saidaComAmortizacao;
      resultadoSemAmortizacao = saidaSemAmortizacao;
    } catch (e) {
      erro = e instanceof Error ? e.message : "Erro desconhecido na simulação.";
      resultado = null;
      resultadoSemAmortizacao = null;
    } finally {
      simulando = false;
    }
  }

  async function aoComparar() {
    erro = null;
    tentouSimular = true;
    const mensagemValidacao = validarContrato();
    if (mensagemValidacao) {
      erro = mensagemValidacao;
      return;
    }
    comparando = true;
    try {
      const cenarios = Object.entries(taxasPorCenario).map(([nome, taxa_anual]) => ({ nome, taxa_anual }));
      const saida = await compararCenarios(contrato, amortizacoes, cenarios, aportesRecorrentes);
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
    aportesRecorrentes = [];
    cenarioNome = CENARIOS_POR_INDEXADOR.tr[0].nome;
    taxaIndexadorPersonalizada = "";
    resultado = null;
    resultadoSemAmortizacao = null;
    comparacao = null;
    erro = null;
  }
</script>

<header class="barra-topo">
  <div class="marca">
    <Logo tamanho={30} />
    <span class="nome-marca">HomePilot</span>
  </div>
  {#if usuario}
    <div class="area-usuario">
      <span>Olá, {usuario.nome.split(" ")[0]}</span>
      <button class="botao-sair" on:click={sair}>Sair</button>
    </div>
  {/if}
</header>

{#if verificandoSessao}
  <p class="carregando-sessao">Carregando...</p>
{:else if !usuario}
  {#if telaAuth === "login"}
    <TelaLogin {aoAutenticar} irParaCadastro={() => (telaAuth = "cadastro")} />
  {:else}
    <TelaCadastro {aoAutenticar} irParaLogin={() => (telaAuth = "login")} />
  {/if}
{:else}
  <main>
    <p class="subtitulo">Planejamento inteligente para financiamento imobiliário</p>
    <FormularioContrato
      bind:contrato
      bind:cenarioNome
      bind:taxaIndexadorPersonalizada
      {camposFaltando}
      {indexadorPersonalizadaFaltando}
    />
    <AmortizacoesExtras bind:amortizacoes bind:aportesRecorrentes />

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
      <GraficoSaldo parcelas={resultado.parcelas} parcelasSemAmortizacao={resultadoSemAmortizacao?.parcelas} />
      <GraficoPrestacao
        parcelas={resultado.parcelas}
        limitePrestacao={contrato.limite_prestacao}
        parcelasSemAmortizacao={resultadoSemAmortizacao?.parcelas}
      />
      <GraficoComposicao parcelas={resultado.parcelas} />
      <TabelaCronograma parcelas={resultado.parcelas} />
    {/if}

    <ComparacaoCenarios resultados={comparacao} executando={comparando} aoComparar={aoComparar} />
  </main>
{/if}

<style>
  .barra-topo {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.85rem 1.5rem;
    background: var(--cor-superficie);
    border-bottom: 1px solid var(--cor-borda);
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .marca {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .nome-marca {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--cor-texto);
    letter-spacing: -0.02em;
  }
  .area-usuario {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    font-size: 0.9rem;
    color: var(--cor-texto-secundario);
  }
  .botao-sair {
    background: none;
    border: 1px solid var(--cor-borda);
    color: var(--cor-texto);
    padding: 0.4rem 0.9rem;
    border-radius: var(--raio-sm);
    cursor: pointer;
    font-size: 0.85rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .botao-sair:hover {
    background: var(--cor-fundo);
    border-color: #c9cdd4;
  }
  .carregando-sessao {
    text-align: center;
    padding: 3rem;
    color: var(--cor-texto-secundario);
  }
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem 1.25rem 3rem;
  }
  .subtitulo {
    color: var(--cor-texto-secundario);
    margin: 0 0 1.25rem 0;
    font-size: 0.95rem;
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
    padding: 0.65rem 1.5rem;
    border-radius: var(--raio-sm);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  .primario:hover:not(:disabled) {
    background: var(--cor-destaque-hover);
  }
  .primario:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .secundario {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    color: var(--cor-texto);
    padding: 0.6rem 1.3rem;
    border-radius: var(--raio-sm);
    cursor: pointer;
    font-size: 0.95rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .secundario:hover {
    background: var(--cor-fundo);
    border-color: #c9cdd4;
  }
  .erro {
    background: var(--cor-perigo-fundo);
    color: #a12020;
    padding: 0.75rem 1rem;
    border-radius: var(--raio-sm);
    margin-bottom: 1rem;
  }
</style>
