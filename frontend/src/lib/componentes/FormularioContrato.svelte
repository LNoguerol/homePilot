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
  .grade {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.9rem;
  }
  label {
    display: flex;
    flex-direction: column;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--cor-texto-secundario);
    gap: 0.35rem;
  }
  input,
  select {
    padding: 0.5rem 0.65rem;
    border-radius: var(--raio-sm);
    border: 1px solid var(--cor-borda);
    background: var(--cor-superficie);
    color: var(--cor-texto);
    font-size: 0.9rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  input:focus,
  select:focus {
    border-color: var(--cor-destaque);
    box-shadow: 0 0 0 3px var(--cor-destaque-fundo);
  }
</style>
