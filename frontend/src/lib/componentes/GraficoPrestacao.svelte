<script lang="ts">
  import { Chart, registerables } from "chart.js";
  import { onDestroy, onMount } from "svelte";
  import type { ParcelaMensal } from "../tipos";
  import { formatarCompetencia } from "../moeda";

  Chart.register(...registerables);

  export let parcelas: ParcelaMensal[];
  export let limitePrestacao: string;

  let canvas: HTMLCanvasElement;
  let grafico: Chart | undefined;

  function montar() {
    if (grafico) grafico.destroy();
    grafico = new Chart(canvas, {
      type: "line",
      data: {
        labels: parcelas.map((p) => formatarCompetencia(p.competencia)),
        datasets: [
          {
            label: "Prestação total (R$)",
            data: parcelas.map((p) => Number(p.prestacao_total)),
            borderColor: "#3a6ea5",
            backgroundColor: "#3a6ea522",
            tension: 0.15,
            fill: true,
          },
          {
            label: "Limite da prestação",
            data: parcelas.map(() => Number(limitePrestacao)),
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
              label: (ctx) => `R$ ${Number(ctx.raw).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`,
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
  $: if (canvas && parcelas) montar();
  onDestroy(() => grafico?.destroy());
</script>

<div class="grafico-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .grafico-container {
    background: var(--cor-cartao);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
</style>
