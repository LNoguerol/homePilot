<script lang="ts">
  import Logo from "./Logo.svelte";

  export let irParaCadastro: () => void;
  export let irParaLogin: () => void;

  const recursos = [
    {
      titulo: "Price ou SAC, lado a lado",
      texto:
        "Simule os dois sistemas de amortização com o mesmo contrato e compare prestação, saldo devedor e juros totais sem refazer nada.",
    },
    {
      titulo: "TR ou poupança como indexador",
      texto:
        "Escolha o indexador do seu contrato e teste cenários de taxa anual — do mais otimista ao mais conservador — para ver o efeito real no seu saldo.",
    },
    {
      titulo: "Amortizações extraordinárias",
      texto:
        "Cadastre aportes pontuais (FGTS, 13º) e recorrentes (\"R$ 500 a mais todo mês\") e veja o impacto de reduzir prazo ou reduzir prestação.",
    },
    {
      titulo: "Alertas de limite",
      texto:
        "Defina o teto de saldo devedor e de prestação que cabem no seu orçamento e acompanhe mês a mês se o financiamento continua dentro deles.",
    },
    {
      titulo: "Comparação de cenários",
      texto:
        "Rode de uma vez os cenários padrão do indexador e veja quitação estimada, maior saldo e juros totais em cada um, lado a lado.",
    },
    {
      titulo: "Exporte para a planilha",
      texto:
        "Baixe o cronograma completo em CSV, pronto para abrir no Excel ou LibreOffice, sem problemas de acentuação ou de casas decimais.",
    },
  ];

  const passos = [
    { numero: "1", texto: "Informe o saldo devedor, a taxa e o indexador do seu contrato de financiamento." },
    { numero: "2", texto: "Adicione as amortizações extras que você já planeja fazer, se houver." },
    { numero: "3", texto: "Simule e acompanhe gráficos, cronograma mensal e alertas de limite em tempo real." },
  ];
</script>

<div class="landing">
  <section class="hero">
    <div class="marca-hero">
      <Logo tamanho={40} />
      <span class="nome-marca">HomePilot</span>
    </div>
    <h1>Enxergue todo o seu financiamento imobiliário antes de assinar embaixo</h1>
    <p class="subtitulo-hero">
      Simule financiamentos pela Tabela Price ou pelo SAC, corrigidos por TR ou poupança, e veja o efeito real de
      cada amortização extraordinária no seu prazo e na sua prestação — antes de decidir o que fazer com o
      próximo FGTS ou 13º.
    </p>
    <div class="acoes-hero">
      <button class="primario" on:click={irParaCadastro}>Criar conta grátis</button>
      <button class="secundario" on:click={irParaLogin}>Já tenho conta</button>
    </div>
  </section>

  <section class="recursos">
    <h2>Tudo o que você precisa para planejar a quitação</h2>
    <div class="grade-recursos">
      {#each recursos as recurso}
        <div class="cartao-recurso">
          <h3>{recurso.titulo}</h3>
          <p>{recurso.texto}</p>
        </div>
      {/each}
    </div>
  </section>

  <section class="como-funciona">
    <h2>Como funciona</h2>
    <div class="grade-passos">
      {#each passos as passo}
        <div class="passo">
          <span class="numero-passo">{passo.numero}</span>
          <p>{passo.texto}</p>
        </div>
      {/each}
    </div>
  </section>

  <section class="cta-final">
    <h2>Pare de simular financiamento na calculadora</h2>
    <p>Crie sua conta gratuita e monte sua primeira simulação em poucos minutos.</p>
    <button class="primario" on:click={irParaCadastro}>Criar conta grátis</button>
  </section>

  <footer class="rodape-landing">
    <p>
      O HomePilot é uma ferramenta educacional e de planejamento. Os resultados são estimativas e não substituem
      o demonstrativo oficial da sua instituição financeira, nem orientação jurídica, contábil ou financeira.
    </p>
  </footer>
</div>

<style>
  .landing {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 1.25rem 3rem;
  }

  section {
    padding: 3.5rem 0;
  }

  h1,
  h2 {
    margin: 0;
  }

  .hero {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 3rem;
  }

  .marca-hero {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1.5rem;
  }

  .nome-marca {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--cor-texto);
    letter-spacing: -0.02em;
  }

  .hero h1 {
    font-size: 2.3rem;
    line-height: 1.25;
    max-width: 42rem;
    color: var(--cor-texto);
  }

  .subtitulo-hero {
    font-size: 1.05rem;
    color: var(--cor-texto-secundario);
    max-width: 38rem;
    margin: 1.25rem 0 0 0;
    line-height: 1.6;
  }

  .acoes-hero {
    display: flex;
    gap: 0.85rem;
    margin-top: 2rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .primario {
    background: var(--cor-destaque);
    color: white;
    border: none;
    padding: 0.75rem 1.75rem;
    border-radius: var(--raio-sm);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .primario:hover {
    background: var(--cor-destaque-hover);
  }

  .secundario {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    color: var(--cor-texto);
    padding: 0.7rem 1.65rem;
    border-radius: var(--raio-sm);
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .secundario:hover {
    background: var(--cor-fundo);
    border-color: #c9cdd4;
  }

  .recursos h2,
  .como-funciona h2,
  .cta-final h2 {
    text-align: center;
    font-size: 1.6rem;
    color: var(--cor-texto);
    margin-bottom: 2rem;
  }

  .grade-recursos {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.25rem;
  }

  .cartao-recurso {
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    box-shadow: var(--sombra-cartao);
    border-radius: var(--raio-md);
    padding: 1.5rem;
  }

  .cartao-recurso h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.05rem;
    color: var(--cor-texto);
  }

  .cartao-recurso p {
    margin: 0;
    font-size: 0.9rem;
    color: var(--cor-texto-secundario);
    line-height: 1.55;
  }

  .grade-passos {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.5rem;
  }

  .passo {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.75rem;
  }

  .numero-passo {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: var(--cor-destaque-fundo);
    color: var(--cor-destaque);
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
  }

  .passo p {
    margin: 0;
    color: var(--cor-texto-secundario);
    font-size: 0.92rem;
    line-height: 1.55;
  }

  .cta-final {
    text-align: center;
    background: var(--cor-superficie);
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio-md);
    padding: 3rem 1.5rem;
  }

  .cta-final p {
    color: var(--cor-texto-secundario);
    margin: 0 0 1.5rem 0;
  }

  .rodape-landing {
    padding: 1.5rem 0 0 0;
    text-align: center;
  }

  .rodape-landing p {
    font-size: 0.8rem;
    color: var(--cor-texto-secundario);
    max-width: 40rem;
    margin: 0 auto;
    line-height: 1.5;
  }

  @media (max-width: 600px) {
    .hero h1 {
      font-size: 1.7rem;
    }
  }
</style>
