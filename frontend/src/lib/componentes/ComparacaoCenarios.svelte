<script lang="ts">
  import type { ResumoCenario } from "../tipos";
  import { formatarMoeda, formatarCompetencia } from "../moeda";

  export let resultados: ResumoCenario[] | null;
  export let executando: boolean;
  export let aoComparar: () => void;
</script>

<section class="secao">
  <div class="cabecalho">
    <h3>Comparação de cenários do indexador</h3>
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
            <th>Total do indexador</th>
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
              <td>{formatarMoeda(r.resumo.total_correcao_indexador)}</td>
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
  td.ok {
    color: var(--cor-destaque);
    font-weight: 600;
  }
</style>
