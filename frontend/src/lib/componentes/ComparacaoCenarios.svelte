<script lang="ts">
  import type { ResumoCenario } from "../tipos";
  import { formatarMoeda, formatarCompetencia } from "../moeda";

  export let resultados: ResumoCenario[] | null;
  export let executando: boolean;
  export let aoComparar: () => void;
</script>

<section class="secao">
  <div class="cabecalho">
    <h3>Comparação de cenários de TR</h3>
    <button class="secundario" on:click={aoComparar} disabled={executando}>
      {executando ? "Comparando..." : "Comparar cenários"}
    </button>
  </div>

  {#if resultados}
    <div class="tabela-scroll">
      <table>
        <thead>
          <tr>
            <th>Cenário</th>
            <th>Quitação estimada</th>
            <th>Maior saldo</th>
            <th>Maior prestação</th>
            <th>Juros totais</th>
            <th>Total da TR</th>
            <th>Limite de saldo</th>
            <th>Limite de prestação</th>
          </tr>
        </thead>
        <tbody>
          {#each resultados as r}
            <tr>
              <td>{r.cenario}</td>
              <td>{formatarCompetencia(r.resumo.data_quitacao)}</td>
              <td>{formatarMoeda(r.resumo.maior_saldo_devedor)}</td>
              <td>{formatarMoeda(r.resumo.maior_prestacao_total)}</td>
              <td>{formatarMoeda(r.resumo.total_juros)}</td>
              <td>{formatarMoeda(r.resumo.total_correcao_tr)}</td>
              <td class:ok={r.resumo.status_limite_saldo === "Dentro do limite"}>{r.resumo.status_limite_saldo}</td>
              <td class:ok={r.resumo.status_limite_prestacao === "Dentro do limite"}>{r.resumo.status_limite_prestacao}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>

<style>
  .secao {
    background: var(--cor-cartao);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
  }
  .cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .secundario {
    background: transparent;
    border: 1px solid var(--cor-destaque);
    color: var(--cor-destaque);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    cursor: pointer;
  }
  .tabela-scroll {
    overflow-x: auto;
    margin-top: 0.75rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  th,
  td {
    padding: 0.4rem 0.6rem;
    text-align: right;
    white-space: nowrap;
    border-bottom: 1px solid #eee;
  }
  th:first-child,
  td:first-child {
    text-align: left;
  }
  td.ok {
    color: #2f6f4f;
    font-weight: 600;
  }
</style>
