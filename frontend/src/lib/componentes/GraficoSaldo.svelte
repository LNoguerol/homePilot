<script lang="ts">
  import { Chart, registerables } from "chart.js";
  import { onDestroy, onMount } from "svelte";
  import type { ParcelaMensal } from "../tipos";
  import { formatarCompetencia } from "../moeda";

  Chart.register(...registerables);

  export let parcelas: ParcelaMensal[];

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
            label: "Saldo devedor (R$)",
            data: parcelas.map((p) => Number(p.saldo_final)),
            borderColor: "#2f6f4f",
            backgroundColor: "#2f6f4f22",
            tension: 0.15,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: { display: true, text: "Evolução mensal do saldo devedor" },
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
