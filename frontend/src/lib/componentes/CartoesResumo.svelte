<script lang="ts">
  import type { ResumoSimulacao } from "../tipos";
  import { formatarMoeda, formatarCompetencia } from "../moeda";
  import Ajuda from "./Ajuda.svelte";

  export let resumo: ResumoSimulacao;

  const textos = {
    maiorSaldo:
      "O maior saldo devedor alcançado em todo o cronograma. Na Price com TR ele pode ficar acima do saldo de hoje nos primeiros anos, porque a correção monetária supera a amortização — no SAC isso não acontece.",
    maiorPrestacao:
      "A maior prestação total (já com seguros e tarifas) de todo o cronograma: o pior mês para o seu orçamento. Na Price com TR ela tende a ser no fim do contrato; no SAC, no começo.",
    quitacao:
      "Mês em que o saldo chega a zero, com o total de meses simulados e quantos foram antecipados em relação ao prazo restante que você informou no contrato.",
    juros:
      "Soma apenas dos juros de todos os meses. Não inclui a correção pela TR nem seguros e tarifas — essas colunas aparecem separadas na tabela mensal.",
    aportes:
      "Total efetivamente abatido do saldo pelos aportes extraordinários. É o valor aportado, não a economia de juros que ele gerou — para medir a economia, compare os juros totais desta simulação com uma simulação sem aportes.",
    limites:
      "Confronto do cronograma com os dois limites que você configurou no formulário. “Ultrapassado” significa que pelo menos um mês passou do limite; esses meses ficam destacados na tabela mensal.",
  };

  $: totalAportado =
    Number(resumo.total_amortizado_extraordinario) > 0
      ? Number(resumo.total_amortizado_extraordinario)
      : 0;
</script>

<section class="cartoes">
  <div class="cartao">
    <span class="rotulo">
      Saldo projetado máximo
      <Ajuda rotulo="o saldo projetado máximo" texto={textos.maiorSaldo} />
    </span>
    <span class="valor">{formatarMoeda(resumo.maior_saldo_devedor)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">
      Prestação máxima
      <Ajuda rotulo="a prestação máxima" texto={textos.maiorPrestacao} />
    </span>
    <span class="valor">{formatarMoeda(resumo.maior_prestacao_total)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">
      Quitação estimada
      <Ajuda rotulo="a quitação estimada" texto={textos.quitacao} />
    </span>
    <span class="valor">{formatarCompetencia(resumo.data_quitacao)}</span>
    <span class="detalhe">{resumo.meses_ate_quitacao} meses ({resumo.meses_antecipados} antecipados)</span>
  </div>
  <div class="cartao">
    <span class="rotulo">
      Juros totais
      <Ajuda rotulo="os juros totais" texto={textos.juros} />
    </span>
    <span class="valor">{formatarMoeda(resumo.total_juros)}</span>
  </div>
  <div class="cartao">
    <span class="rotulo">
      Total aportado
      <Ajuda rotulo="o total aportado" texto={textos.aportes} />
    </span>
    <span class="valor">{formatarMoeda(totalAportado)}</span>
  </div>
  <div class="cartao" class:alerta={resumo.status_limite_saldo === "Ultrapassado" || resumo.status_limite_prestacao === "Ultrapassado"}>
    <span class="rotulo">
      Situação dos limites
      <Ajuda rotulo="a situação dos limites" texto={textos.limites} />
    </span>
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
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.1rem 1.3rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    border-left: 3px solid var(--cor-destaque);
  }
  .cartao.alerta {
    border-left-color: var(--cor-perigo);
  }
  .rotulo {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--cor-texto-secundario);
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }
  .valor {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--cor-texto);
  }
  .detalhe {
    font-size: 0.78rem;
    color: var(--cor-texto-secundario);
  }
</style>
