<script lang="ts">
  import type { AmortizacaoExtraordinaria, AporteRecorrente } from "../tipos";
  import Ajuda from "./Ajuda.svelte";
  import { formatarMoeda } from "../moeda";

  export let amortizacoes: AmortizacaoExtraordinaria[];
  export let aporteRecorrente: AporteRecorrente | null;

  const textos = {
    recorrente:
      "Um aporte que se repete, para não precisar cadastrar centenas de linhas. “R$ 500 a cada 1 mês até quitar” é o caso mais comum: pagar um pouco além da prestação todo mês. Com periodicidade 24, expressa o saque bienal do FGTS.",
    periodicidade:
      "De quantos em quantos meses o aporte se repete. 1 = todo mês; 12 = uma vez por ano; 24 = a cada dois anos. A contagem é ancorada no mês inicial.",
    mesInicial:
      "Primeira competência em que o aporte entra. Não pode ser anterior ao mês da data-base do contrato.",
    ate:
      "“Quitar o financiamento” repete o aporte enquanto houver saldo — é o que você quer se pretende manter o esforço até o fim. “Um mês específico” encerra a recorrência numa competência escolhida.",
    pontuais:
      "Aportes avulsos, para o que não é regular: FGTS, 13º, bônus, venda de um bem. Se um pontual cair no mesmo mês do recorrente, os dois valores somam.",
    data:
      "Mês em que o aporte entra. Só o mês e o ano importam — o dia é ignorado na hora de casar o aporte com o cronograma. Não pode ser anterior à data-base do contrato.",
    valor:
      "Quanto será abatido do saldo. Se o valor for maior que o saldo daquele mês, apenas o necessário é usado e o financiamento é quitado ali mesmo.",
    estrategia:
      "Redução do prazo mantém a parcela no patamar em que estava e antecipa a quitação — costuma economizar mais juros. Redução da prestação mantém o prazo e diminui a parcela dos meses seguintes, aliviando o orçamento.",
  };

  // O backend espera datas completas (YYYY-MM-DD), mas a recorrência raciocina em
  // competências. A tela usa <input type="month"> e o dia fica fixo em 01.
  const paraMes = (data: string | null) => (data ? data.slice(0, 7) : "");
  const paraData = (mes: string) => (mes ? `${mes}-01` : "");

  function recorrentePadrao(): AporteRecorrente {
    return {
      valor: "500.00",
      periodicidade_meses: 1,
      mes_inicial: paraData(new Date().toISOString().slice(0, 7)),
      mes_final: null,
      estrategia: "reducao_prazo",
    };
  }

  function alternarRecorrente(ativo: boolean) {
    aporteRecorrente = ativo ? recorrentePadrao() : null;
  }

  function alternarFim(modo: string) {
    if (!aporteRecorrente) return;
    aporteRecorrente.mes_final =
      modo === "quitar" ? null : paraData(paraMes(aporteRecorrente.mes_inicial));
  }

  /** Quantas competências a recorrência abrange, quando ela tem fim definido.
   * Sem mês final não há como saber sem simular, e nesse caso devolve `null` em
   * vez de estimar um número que poderia não se confirmar. */
  function contarAportes(r: AporteRecorrente): number | null {
    if (!r.mes_final) return null;
    const [anoInicial, mesInicial] = paraMes(r.mes_inicial).split("-").map(Number);
    const [anoFinal, mesFinal] = paraMes(r.mes_final).split("-").map(Number);
    if (!anoInicial || !anoFinal) return null;
    const meses = (anoFinal - anoInicial) * 12 + (mesFinal - mesInicial);
    if (meses < 0) return null;
    return Math.floor(meses / Math.max(1, r.periodicidade_meses)) + 1;
  }

  $: quantidade = aporteRecorrente ? contarAportes(aporteRecorrente) : null;
  $: totalPrevisto =
    aporteRecorrente && quantidade !== null ? quantidade * Number(aporteRecorrente.valor) : null;

  function adicionar() {
    amortizacoes = [...amortizacoes, { data: "2027-06-17", valor: "40000.00", estrategia: "reducao_prazo" }];
  }

  function remover(indice: number) {
    amortizacoes = amortizacoes.filter((_, i) => i !== indice);
  }

  function limparTodos() {
    amortizacoes = [];
  }
</script>

<section class="secao">
  <h3>Amortizações extraordinárias</h3>

  <div class="recorrente" class:ativo={aporteRecorrente !== null}>
    <label class="ativar">
      <input
        type="checkbox"
        checked={aporteRecorrente !== null}
        on:change={(e) => alternarRecorrente(e.currentTarget.checked)}
      />
      <span class="titulo-bloco">
        Aporte recorrente
        <Ajuda rotulo="o aporte recorrente" texto={textos.recorrente} />
      </span>
    </label>

    {#if aporteRecorrente}
      <div class="grade-recorrente">
        <label>
          <span class="rotulo-linha">
            Valor (R$)
            <Ajuda rotulo="o valor do aporte recorrente" texto={textos.valor} />
          </span>
          <input type="number" step="0.01" bind:value={aporteRecorrente.valor} />
        </label>
        <label>
          <span class="rotulo-linha">
            A cada (meses)
            <Ajuda rotulo="a periodicidade" texto={textos.periodicidade} />
          </span>
          <input type="number" min="1" bind:value={aporteRecorrente.periodicidade_meses} />
        </label>
        <label>
          <span class="rotulo-linha">
            A partir de
            <Ajuda rotulo="o mês inicial" texto={textos.mesInicial} />
          </span>
          <input
            type="month"
            value={paraMes(aporteRecorrente.mes_inicial)}
            on:input={(e) =>
              aporteRecorrente && (aporteRecorrente.mes_inicial = paraData(e.currentTarget.value))}
          />
        </label>
        <label>
          <span class="rotulo-linha">
            Até
            <Ajuda rotulo="o fim da recorrência" texto={textos.ate} />
          </span>
          <select
            value={aporteRecorrente.mes_final ? "data" : "quitar"}
            on:change={(e) => alternarFim(e.currentTarget.value)}
          >
            <option value="quitar">Quitar o financiamento</option>
            <option value="data">Um mês específico</option>
          </select>
        </label>
        {#if aporteRecorrente.mes_final}
          <label>
            <span class="rotulo-linha">Último mês</span>
            <input
              type="month"
              value={paraMes(aporteRecorrente.mes_final)}
              on:input={(e) =>
                aporteRecorrente && (aporteRecorrente.mes_final = paraData(e.currentTarget.value))}
            />
          </label>
        {/if}
        <label>
          <span class="rotulo-linha">
            Estratégia
            <Ajuda rotulo="a estratégia do aporte recorrente" texto={textos.estrategia} />
          </span>
          <select bind:value={aporteRecorrente.estrategia}>
            <option value="reducao_prazo">Redução do prazo</option>
            <option value="reducao_prestacao">Redução da prestação</option>
          </select>
        </label>
      </div>

      <p class="previsao">
        {#if totalPrevisto !== null}
          {quantidade} aportes de {formatarMoeda(aporteRecorrente.valor)} · total {formatarMoeda(
            totalPrevisto,
          )}
        {:else}
          {formatarMoeda(aporteRecorrente.valor)} a cada {aporteRecorrente.periodicidade_meses === 1
            ? "mês"
            : `${aporteRecorrente.periodicidade_meses} meses`}, até quitar — o total aparece no resumo
          depois de simular.
        {/if}
      </p>
    {/if}
  </div>

  <div class="cabecalho-pontuais">
    <span class="titulo-bloco">
      Aportes pontuais
      <Ajuda rotulo="os aportes pontuais" texto={textos.pontuais} />
    </span>
    <div class="acoes">
      <button class="secundario" on:click={adicionar}>Adicionar</button>
      {#if amortizacoes.length > 0}
        <button class="secundario" on:click={limparTodos}>Limpar todos</button>
      {/if}
    </div>
  </div>

  {#if amortizacoes.length === 0}
    <p class="vazio">Nenhum aporte pontual cadastrado.</p>
  {:else}
    <div class="lista">
      {#each amortizacoes as amortizacao, indice}
        <div class="linha">
          <label>
            <span class="rotulo-linha">
              Data
              <Ajuda rotulo="a data do aporte" texto={textos.data} />
            </span>
            <input type="date" bind:value={amortizacao.data} />
          </label>
          <label>
            <span class="rotulo-linha">
              Valor (R$)
              <Ajuda rotulo="o valor do aporte" texto={textos.valor} />
            </span>
            <input type="number" step="0.01" bind:value={amortizacao.valor} />
          </label>
          <label>
            <span class="rotulo-linha">
              Estratégia
              <Ajuda rotulo="a estratégia do aporte" texto={textos.estrategia} />
            </span>
            <select bind:value={amortizacao.estrategia}>
              <option value="reducao_prazo">Redução do prazo</option>
              <option value="reducao_prestacao">Redução da prestação</option>
            </select>
          </label>
          <button class="remover" on:click={() => remover(indice)} title="Excluir amortização">✕</button>
        </div>
      {/each}
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
    margin: 0 0 0.9rem 0;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--cor-destaque);
  }
  .rotulo-linha {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }
  .titulo-bloco {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--cor-texto);
  }
  .recorrente {
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio-sm);
    padding: 0.9rem 1rem;
    margin-bottom: 1.25rem;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .recorrente.ativo {
    background: var(--cor-destaque-fundo);
    border-color: var(--cor-destaque);
  }
  .ativar {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }
  .ativar input {
    width: 15px;
    height: 15px;
    accent-color: var(--cor-destaque);
    cursor: pointer;
  }
  .grade-recorrente {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.7rem;
    margin-top: 0.9rem;
  }
  .previsao {
    margin: 0.85rem 0 0 0;
    font-size: 0.8rem;
    line-height: 1.5;
    color: var(--cor-destaque);
    font-weight: 500;
  }
  .cabecalho-pontuais {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.8rem;
  }
  .acoes {
    display: flex;
    gap: 0.5rem;
  }
  .vazio {
    margin: 0;
    font-size: 0.82rem;
    color: var(--cor-texto-secundario);
  }
  .lista {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
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
</style>
