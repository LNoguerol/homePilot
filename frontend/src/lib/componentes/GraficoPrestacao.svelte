<script lang="ts">
  import { Chart, registerables } from "chart.js";
  import { onDestroy, onMount } from "svelte";
  import type { ParcelaMensal } from "../tipos";
  import { formatarCompetencia } from "../moeda";

  Chart.register(...registerables);

  export let parcelas: ParcelaMensal[];
  export let limitePrestacao: string;
  export let parcelasSemAmortizacao: ParcelaMensal[] | undefined = undefined;

  let canvas: HTMLCanvasElement;
  let grafico: Chart | undefined;

  /** Após a quitação, uma das duas séries pode ser mais curta que a outra —
   * usa a competência (não o índice) para alinhar os pontos e completa o que
   * já foi quitado com prestação zero, em vez de truncar o eixo X pela mais curta. */
  function construirSerie(base: ParcelaMensal[], competencias: string[]): number[] {
    const porCompetencia = new Map(base.map((p) => [p.competencia, Number(p.prestacao_total)]));
    return competencias.map((competencia) => porCompetencia.get(competencia) ?? 0);
  }

  function montar() {
    if (grafico) grafico.destroy();
    const parcelasReferencia =
      parcelasSemAmortizacao && parcelasSemAmortizacao.length > parcelas.length ? parcelasSemAmortizacao : parcelas;
    const competencias = parcelasReferencia.map((p) => p.competencia);

    grafico = new Chart(canvas, {
      type: "line",
      data: {
        labels: competencias.map(formatarCompetencia),
        datasets: [
          {
            label: "Prestação total (R$)",
            data: construirSerie(parcelas, competencias),
            borderColor: "#3a6ea5",
            backgroundColor: "#3a6ea522",
            tension: 0.15,
            fill: true,
          },
          ...(parcelasSemAmortizacao
            ? [
                {
                  label: "Prestação sem amortização extra (R$)",
                  data: construirSerie(parcelasSemAmortizacao, competencias),
                  borderColor: "#8a8f98",
                  backgroundColor: "transparent",
                  borderDash: [6, 4],
                  tension: 0.15,
                  fill: false,
                  pointRadius: 0,
                },
              ]
            : []),
          {
            label: "Limite da prestação",
            data: competencias.map(() => Number(limitePrestacao)),
            borderColor: "#d64545",
            borderDash: [6, 4],
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: { display: true, text: "Evolução da prestação total" },
          tooltip: {
            callbacks: {
              label: (ctx) =>
                `${ctx.dataset.label}: R$ ${Number(ctx.raw).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`,
            },
          },
        },
        scales: {
          y: { title: { display: true, text: "R$" } },
        },
      },
    });
  }

  onMount(montar);
  $: if (canvas && parcelas) {
    parcelasSemAmortizacao;
    montar();
  }
  onDestroy(() => grafico?.destroy());
</script>

<div class="grafico-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .grafico-container {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.25rem;
    margin-bottom: 1.25rem;
  }
</style>
