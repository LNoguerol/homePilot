<script lang="ts">
  import type { ResumoSimulacao } from "../tipos";
  import { formatarMoeda, formatarCompetencia } from "../moeda";

  export let resumo: ResumoSimulacao;

  $: economiaEstimada =
    Number(resumo.total_amortizado_extraordinario) > 0
      ? Number(resumo.total_amortizado_extraordinario)
      : 0;
</script>

<section class="cartoes">
  <div class="cartao">
    <span class="rotulo">Saldo projetado máximo</span>
    <span class="valor">{formatarMoeda(resumo.maior_saldo_devedor)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">Prestação máxima</span>
    <span class="valor">{formatarMoeda(resumo.maior_prestacao_total)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">Quitação estimada</span>
    <span class="valor">{formatarCompetencia(resumo.data_quitacao)}</span>
    <span class="detalhe">{resumo.meses_ate_quitacao} meses ({resumo.meses_antecipados} antecipados)</span>
  </div>
  <div class="cartao">
    <span class="rotulo">Juros totais</span>
    <span class="valor">{formatarMoeda(resumo.total_juros)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">Economia estimada (aportes extraordinários)</span>
    <span class="valor">{formatarMoeda(economiaEstimada)}</span>
  </div>
  <div class="cartao" class:alerta={resumo.status_limite_saldo === "Ultrapassado" || resumo.status_limite_prestacao === "Ultrapassado"}>
    <span class="rotulo">Situação dos limites</span>
    <span class="valor">Saldo: {resumo.status_limite_saldo}</span>
    <span class="valor">Prestação: {resumo.status_limite_prestacao}</span>
  </div>
</section>

<style>
  .cartoes {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  .cartao {
    background: var(--cor-cartao);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    border-left: 4px solid var(--cor-destaque);
  }
  .cartao.alerta {
    border-left-color: #d64545;
  }
  .rotulo {
    font-size: 0.78rem;
    color: #666;
  }
  .valor {
    font-size: 1.15rem;
    font-weight: 600;
  }
  .detalhe {
    font-size: 0.78rem;
    color: #888;
  }
</style>
