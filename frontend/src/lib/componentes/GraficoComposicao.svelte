<script lang="ts">
  import { Chart, registerables } from "chart.js";
  import { onDestroy, onMount } from "svelte";
  import type { ParcelaMensal } from "../tipos";
  import { formatarCompetencia } from "../moeda";

  Chart.register(...registerables);

  export let parcelas: ParcelaMensal[];

  let canvas: HTMLCanvasElement;
  let grafico: Chart | undefined;

  function acumular(campo: keyof ParcelaMensal): number[] {
    let acumulado = 0;
    return parcelas.map((p) => {
      acumulado += Number(p[campo]);
      return acumulado;
    });
  }

  function montar() {
    if (grafico) grafico.destroy();
    grafico = new Chart(canvas, {
      type: "line",
      data: {
        labels: parcelas.map((p) => formatarCompetencia(p.competencia)),
        datasets: [
          { label: "Juros acumulados", data: acumular("juros"), borderColor: "#c9752c", fill: false },
          {
            label: "Amortização acumulada",
            data: acumular("amortizacao_ordinaria").map(
              (v, i) => v + acumular("amortizacao_extraordinaria")[i],
            ),
            borderColor: "#1f6b4e",
            fill: false,
          },
          {
            label: "Correção do indexador acumulada",
            data: acumular("correcao_indexador"),
            borderColor: "#8a4fd6",
            fill: false,
          },
          {
            label: "Seguros e tarifas acumulados",
            data: acumular("seguros_tarifas"),
            borderColor: "#3a6ea5",
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: { display: true, text: "Composição acumulada do financiamento" },
          tooltip: {
            callbacks: {
              label: (ctx) =>
                `${ctx.dataset.label}: R$ ${Number(ctx.raw).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`,
            },
          },
        },
        scales: {
          y: { title: { display: true, text: "R$ acumulado" } },
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
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.25rem;
    margin-bottom: 1.25rem;
  }
</style>
