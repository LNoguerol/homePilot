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
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
  }
  .secao h3 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--cor-destaque);
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
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    color: var(--cor-texto);
    padding: 0.45rem 0.9rem;
    border-radius: var(--raio-sm);
    cursor: pointer;
    font-size: 0.85rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .secundario:hover {
    background: var(--cor-fundo);
    border-color: #c9cdd4;
  }
  .tabela-scroll {
    overflow-x: auto;
    margin-top: 0.9rem;
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
    padding: 0.5rem 0.65rem;
    text-align: right;
    white-space: nowrap;
    border-bottom: 1px solid var(--cor-borda);
  }
  th {
    text-transform: uppercase;
    letter-spacing: 0.02em;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--cor-texto-secundario);
  }
  th:first-child,
  td:first-child {
    text-align: left;
  }
  tbody tr:hover td {
    background: var(--cor-fundo);
  }
  tr.alerta td {
    background: var(--cor-perigo-fundo);
  }
</style>
