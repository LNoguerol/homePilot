<script lang="ts">
  import type { ParcelaMensal } from "../tipos";
  import { formatarMoeda, formatarCompetencia } from "../moeda";
  import { exportarCronogramaCsv } from "../csv";

  export let parcelas: ParcelaMensal[];

  let visivel = false;
</script>

<section class="secao">
  <div class="cabecalho">
    <h3>Tabela mensal</h3>
    <div class="acoes">
      <button class="secundario" on:click={() => (visivel = !visivel)}>
        {visivel ? "Ocultar tabela" : "Exibir tabela"}
      </button>
      <button class="secundario" on:click={() => exportarCronogramaCsv(parcelas)}>Exportar CSV</button>
    </div>
  </div>

  {#if visivel}
    <div class="tabela-scroll">
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Saldo inicial</th>
            <th>TR</th>
            <th>Juros</th>
            <th>Amortização</th>
            <th>Amortização extra</th>
            <th>Prestação total</th>
            <th>Saldo final</th>
          </tr>
        </thead>
        <tbody>
          {#each parcelas as p}
            <tr class:alerta={p.alerta_saldo || p.alerta_prestacao}>
              <td>{formatarCompetencia(p.competencia)}</td>
              <td>{formatarMoeda(p.saldo_inicial)}</td>
              <td>{formatarMoeda(p.correcao_tr)}</td>
              <td>{formatarMoeda(p.juros)}</td>
              <td>{formatarMoeda(p.amortizacao_ordinaria)}</td>
              <td>{formatarMoeda(p.amortizacao_extraordinaria)}</td>
              <td>{formatarMoeda(p.prestacao_total)}</td>
              <td>{formatarMoeda(p.saldo_final)}</td>
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
  .acoes {
    display: flex;
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
    max-height: 480px;
    overflow-y: auto;
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
  tr.alerta {
    background: #fdeaea;
  }
</style>
