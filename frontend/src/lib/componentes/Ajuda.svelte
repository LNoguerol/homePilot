<script lang="ts">
  /** Botão discreto de interrogação que revela a explicação de um campo.
   *
   * O balão abre por clique (e não por hover) para funcionar também em toque e
   * por teclado. Fecha ao clicar fora, ao apertar Esc ou ao abrir o balão de
   * outro campo — como o clique no gatilho vizinho é "fora" daqui, o
   * fechamento de um e a abertura do outro acontecem no mesmo clique. */
  export let texto: string;
  /** Nome do campo, usado apenas no rótulo acessível do botão. */
  export let rotulo: string;

  const LARGURA_BALAO = 280;
  const MARGEM_TELA = 16;

  let aberto = false;
  let raiz: HTMLElement;
  let alinharDireita = false;

  function alternar() {
    if (!aberto) {
      // Decide o lado antes de abrir, para o balão não nascer fora da tela.
      // O padrão é crescer para a direita; só vira quando não couber ali E
      // couber do outro lado — virar sempre estouraria a margem esquerda nos
      // campos da primeira coluna.
      const caixa = raiz.getBoundingClientRect();
      const cabeCrescendoParaDireita = caixa.left + LARGURA_BALAO <= window.innerWidth - MARGEM_TELA;
      const cabeCrescendoParaEsquerda = caixa.right - LARGURA_BALAO >= MARGEM_TELA;
      alinharDireita = !cabeCrescendoParaDireita && cabeCrescendoParaEsquerda;
    }
    aberto = !aberto;
  }

  function aoClicarFora(evento: MouseEvent) {
    if (aberto && raiz && !raiz.contains(evento.target as Node)) {
      aberto = false;
    }
  }

  function aoTeclar(evento: KeyboardEvent) {
    if (evento.key === "Escape") {
      aberto = false;
    }
  }
</script>

<svelte:window on:click={aoClicarFora} on:keydown={aoTeclar} />

<!-- preventDefault nos cliques: estes elementos ficam dentro de <label>, e sem
     isso o clique seria repassado ao input/select associado. -->
<span class="raiz" bind:this={raiz}>
  <button
    type="button"
    class="gatilho"
    class:ativo={aberto}
    aria-label={`O que é ${rotulo}?`}
    aria-expanded={aberto}
    on:click|preventDefault={alternar}
  >
    ?
  </button>
  {#if aberto}
    <!-- O on:click aqui não torna o balão interativo: ele só cancela o repasse
         do clique ao input associado ao <label> que envolve este componente.
         Não há comportamento a acessar por teclado, então as duas regras de
         a11y abaixo não se aplicam a este caso. -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <span class="balao" class:direita={alinharDireita} role="tooltip" on:click|preventDefault>
      {texto}
    </span>
  {/if}
</span>

<style>
  .raiz {
    position: relative;
    display: inline-flex;
    /* não encolhe nem quebra linha: quem posiciona é o rótulo (flex), então o
       gatilho fica sempre no mesmo lugar em vez de correr atrás do texto */
    flex: none;
  }
  .gatilho {
    position: relative;
    width: 16px;
    height: 16px;
    padding: 0;
    border-radius: 50%;
    border: 1px solid var(--cor-borda);
    background: var(--cor-superficie);
    color: var(--cor-texto-secundario);
    font-size: 0.62rem;
    font-weight: 700;
    line-height: 1;
    cursor: help;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  /* área de toque de 28px sem aumentar o círculo visível — o alvo de 16px
     sozinho seria pequeno demais para dedo em tela de celular */
  .gatilho::after {
    content: "";
    position: absolute;
    inset: -6px;
  }
  .gatilho:hover,
  .gatilho.ativo {
    background: var(--cor-destaque-fundo);
    border-color: var(--cor-destaque);
    color: var(--cor-destaque);
  }
  .balao {
    position: absolute;
    top: calc(100% + 7px);
    left: 0;
    z-index: 20;
    width: max-content;
    max-width: min(280px, calc(100vw - 2rem));
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio-sm);
    box-shadow: 0 4px 12px rgba(16, 24, 40, 0.1), 0 1px 3px rgba(16, 24, 40, 0.08);
    padding: 0.6rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 400;
    line-height: 1.5;
    color: var(--cor-texto);
    text-transform: none;
    letter-spacing: normal;
    white-space: normal;
    text-align: left;
    cursor: default;
  }
  .balao.direita {
    left: auto;
    right: 0;
  }
</style>
