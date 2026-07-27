<script lang="ts">
  import type { DadosContrato } from "../tipos";

  export let contrato: DadosContrato;
  export let cenarioNome: string;
  export let taxaTrPersonalizada: string;

  const cenarios = [
    { nome: "TR 0,0% a.a.", taxa: "0.0" },
    { nome: "TR 1,5% a.a.", taxa: "0.015" },
    { nome: "TR 2,0% a.a.", taxa: "0.02" },
    { nome: "TR 2,5% a.a.", taxa: "0.025" },
    { nome: "Personalizada", taxa: "custom" },
  ];
</script>

<section class="secao">
  <h3>Dados do contrato</h3>
  <div class="grade">
    <label>
      Data-base
      <input type="date" bind:value={contrato.data_base} />
    </label>
    <label>
      Saldo devedor (R$)
      <input type="number" step="0.01" bind:value={contrato.saldo_devedor} />
    </label>
    <label>
      Prazo original (meses)
      <input type="number" bind:value={contrato.prazo_original} />
    </label>
    <label>
      Prazo restante (meses)
      <input type="number" bind:value={contrato.prazo_restante} />
    </label>
  </div>
</section>

<section class="secao">
  <h3>Taxas e TR</h3>
  <div class="grade">
    <label>
      Taxa nominal anual (fração, ex.: 0,1002 = 10,02%)
      <input type="number" step="0.0001" bind:value={contrato.taxa_nominal_anual} />
    </label>
    <label>
      Taxa efetiva informada (fração, ex.: 0,1049 = 10,49%)
      <input type="number" step="0.0001" bind:value={contrato.taxa_efetiva_informada} />
    </label>
    <label>
      Cenário de TR
      <select bind:value={cenarioNome}>
        {#each cenarios as c}
          <option value={c.nome}>{c.nome}</option>
        {/each}
      </select>
    </label>
    {#if cenarioNome === "Personalizada"}
      <label>
        TR anual personalizada (fração, ex.: 0,02 = 2,0%)
        <input type="number" step="0.0001" bind:value={taxaTrPersonalizada} />
      </label>
    {/if}
  </div>
</section>

<section class="secao">
  <h3>Seguros e tarifas</h3>
  <div class="grade">
    <label>
      Seguros e tarifas mensais (R$)
      <input type="number" step="0.01" bind:value={contrato.seguros_tarifas_mensais} />
    </label>
  </div>
</section>

<section class="secao">
  <h3>Limites financeiros</h3>
  <div class="grade">
    <label>
      Limite máximo do saldo devedor (R$)
      <input type="number" step="0.01" bind:value={contrato.limite_saldo} />
    </label>
    <label>
      Limite máximo da prestação total (R$)
      <input type="number" step="0.01" bind:value={contrato.limite_prestacao} />
    </label>
  </div>
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
  .grade {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
  }
  label {
    display: flex;
    flex-direction: column;
    font-size: 0.85rem;
    gap: 0.25rem;
  }
  input,
  select {
    padding: 0.4rem 0.5rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 0.9rem;
  }
</style>
