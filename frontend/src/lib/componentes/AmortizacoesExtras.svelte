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
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
  }
  .secao h3 {
    margin: 0 0 0.9rem 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--cor-destaque);
  }
  .lista {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-bottom: 0.9rem;
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
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--cor-texto-secundario);
    gap: 0.3rem;
  }
  input,
  select {
    padding: 0.4rem 0.55rem;
    border-radius: var(--raio-sm);
    border: 1px solid var(--cor-borda);
    background: var(--cor-superficie);
    color: var(--cor-texto);
    font-size: 0.85rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  input:focus,
  select:focus {
    border-color: var(--cor-destaque);
    box-shadow: 0 0 0 3px var(--cor-destaque-fundo);
  }
  .remover {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    color: var(--cor-perigo);
    border-radius: var(--raio-sm);
    padding: 0.4rem 0.6rem;
    cursor: pointer;
    height: fit-content;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .remover:hover {
    background: var(--cor-perigo-fundo);
    border-color: var(--cor-perigo);
  }
  .secundario {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    color: var(--cor-texto);
    padding: 0.55rem 1.1rem;
    border-radius: var(--raio-sm);
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .secundario:hover {
    background: var(--cor-fundo);
    border-color: #c9cdd4;
  }
</style>
