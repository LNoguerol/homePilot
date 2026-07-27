<script lang="ts">
  import type { AmortizacaoExtraordinaria } from "../tipos";

  export let amortizacoes: AmortizacaoExtraordinaria[];

  function adicionar() {
    amortizacoes = [...amortizacoes, { data: "2027-06-17", valor: "40000.00", estrategia: "reducao_prazo" }];
  }

  function remover(indice: number) {
    amortizacoes = amortizacoes.filter((_, i) => i !== indice);
  }
</script>

<section class="secao">
  <h3>Amortizações extraordinárias (FGTS)</h3>
  <div class="lista">
    {#each amortizacoes as amortizacao, indice}
      <div class="linha">
        <label>
          Data
          <input type="date" bind:value={amortizacao.data} />
        </label>
        <label>
          Valor (R$)
          <input type="number" step="0.01" bind:value={amortizacao.valor} />
        </label>
        <label>
          Estratégia
          <select bind:value={amortizacao.estrategia}>
            <option value="reducao_prazo">Redução do prazo</option>
            <option value="reducao_prestacao">Redução da prestação</option>
          </select>
        </label>
        <button class="remover" on:click={() => remover(indice)} title="Excluir amortização">✕</button>
      </div>
    {/each}
  </div>
  <button class="secundario" on:click={adicionar}>Adicionar amortização</button>
</section>

<style>
  .secao {
    background: var(--cor-cartao);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
  }
  .secao h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.95rem;
    color: var(--cor-destaque);
  }
  .lista {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
  }
  .linha {
    display: grid;
    grid-template-columns: 1fr 1fr 1.3fr auto;
    gap: 0.5rem;
    align-items: end;
  }
  label {
    display: flex;
    flex-direction: column;
    font-size: 0.8rem;
    gap: 0.25rem;
  }
  input,
  select {
    padding: 0.35rem 0.5rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 0.85rem;
  }
  .remover {
    background: #d64545;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.4rem 0.6rem;
    cursor: pointer;
    height: fit-content;
  }
  .secundario {
    background: transparent;
    border: 1px solid var(--cor-destaque);
    color: var(--cor-destaque);
    padding: 0.45rem 0.9rem;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
