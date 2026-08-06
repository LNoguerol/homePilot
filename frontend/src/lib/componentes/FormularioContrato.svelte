<script lang="ts">
  import type { ContratoExtraido, DadosContrato, Indexador } from "../tipos";
  import Ajuda from "./Ajuda.svelte";
  import { importarContratoPdf } from "../api";
  import { CENARIOS_POR_INDEXADOR, ROTULO_INDEXADOR } from "../cenariosIndexador";

  export let contrato: DadosContrato;
  export let cenarioNome: string;
  export let taxaIndexadorPersonalizada: string;
  export let camposFaltando: Set<keyof DadosContrato> = new Set();
  export let indexadorPersonalizadaFaltando = false;

  let importando = false;
  let mensagemImportacao: string | null = null;
  let erroImportacao: string | null = null;

  const rotulosCampos: Record<keyof ContratoExtraido, string> = {
    data_base: "data-base",
    saldo_devedor: "saldo devedor",
    sistema_amortizacao: "sistema de amortização",
    taxa_nominal_anual: "taxa nominal anual",
    taxa_efetiva_informada: "taxa efetiva informada",
    prazo_original: "prazo original",
    prazo_restante: "prazo restante",
  };

  function aplicar<K extends keyof ContratoExtraido>(
    campo: K,
    valor: ContratoExtraido[K],
    encontrados: string[],
    naoEncontrados: string[],
  ) {
    if (valor === null) {
      naoEncontrados.push(rotulosCampos[campo]);
      return;
    }
    (contrato as unknown as Record<K, NonNullable<ContratoExtraido[K]>>)[campo] = valor;
    encontrados.push(rotulosCampos[campo]);
  }

  function aplicarDadosExtraidos(extraido: ContratoExtraido) {
    const encontrados: string[] = [];
    const naoEncontrados: string[] = [];

    aplicar("data_base", extraido.data_base, encontrados, naoEncontrados);
    aplicar("saldo_devedor", extraido.saldo_devedor, encontrados, naoEncontrados);
    aplicar("sistema_amortizacao", extraido.sistema_amortizacao, encontrados, naoEncontrados);
    aplicar("taxa_nominal_anual", extraido.taxa_nominal_anual, encontrados, naoEncontrados);
    aplicar("taxa_efetiva_informada", extraido.taxa_efetiva_informada, encontrados, naoEncontrados);
    aplicar("prazo_original", extraido.prazo_original, encontrados, naoEncontrados);
    aplicar("prazo_restante", extraido.prazo_restante, encontrados, naoEncontrados);

    contrato = contrato;
    mensagemImportacao =
      encontrados.length > 0
        ? `Importado do PDF: ${encontrados.join(", ")}.` +
          (naoEncontrados.length > 0 ? ` Não encontrado: ${naoEncontrados.join(", ")}.` : "")
        : "Não foi possível reconhecer nenhum campo nesse PDF.";
  }

  async function aoSelecionarArquivo(evento: Event) {
    const entrada = evento.currentTarget as HTMLInputElement;
    const arquivo = entrada.files?.[0];
    if (!arquivo) return;

    importando = true;
    erroImportacao = null;
    mensagemImportacao = null;
    try {
      const extraido = await importarContratoPdf(arquivo);
      aplicarDadosExtraidos(extraido);
    } catch (e) {
      erroImportacao = e instanceof Error ? e.message : "Não foi possível importar o PDF.";
    } finally {
      importando = false;
      entrada.value = "";
    }
  }

  const indexadores = [
    { valor: "tr", rotulo: "TR" },
    { valor: "poupanca", rotulo: "Poupança" },
  ] as const;

  $: cenarios = [...CENARIOS_POR_INDEXADOR[contrato.indexador], { nome: "Personalizada", taxa: "custom" }];

  // Troca de indexador invalida o cenário selecionado (ex.: "TR 1,5% a.a."
  // não existe na lista da poupança) — volta para o primeiro cenário padrão
  // do novo indexador em vez de deixar uma seleção inconsistente.
  let indexadorAnterior: Indexador = contrato.indexador;
  $: if (contrato.indexador !== indexadorAnterior) {
    indexadorAnterior = contrato.indexador;
    cenarioNome = CENARIOS_POR_INDEXADOR[contrato.indexador][0].nome;
    taxaIndexadorPersonalizada = "";
  }

  const sistemas = [
    { valor: "price", rotulo: "Price — prestação constante" },
    { valor: "sac", rotulo: "SAC — amortização constante" },
  ] as const;

  const explicacaoSistema: Record<string, string> = {
    price:
      "Price: a prestação é a grandeza constante e a amortização é o que sobra dela depois de pagar os juros. Começa mais barata, mas amortiza devagar no início e paga mais juros no total. Com o indexador, o saldo pode até crescer nos primeiros anos.",
    sac:
      "SAC: a amortização é a grandeza constante (saldo ÷ prazo) e a prestação é ela mais os juros, por isso a parcela é decrescente. Começa mais caro, mas o saldo cai mais rápido desde o primeiro mês e o total de juros é bem menor.",
  };

  const textos = {
    dataBase:
      "Mês de referência em que a simulação começa — normalmente o mês do extrato que você usou para pegar o saldo. O primeiro mês do cronograma é o mês seguinte a esta data, e o dia informado define o dia de aniversário das parcelas (ajustado automaticamente nos meses mais curtos).",
    saldoDevedor:
      "Quanto você ainda deve hoje, conforme o extrato do banco — não o valor original do financiamento. É o ponto de partida de todo o cálculo.",
    prazoOriginal:
      "Número total de meses contratado no início do financiamento. Não entra em nenhuma fórmula: serve só de referência para mostrar quantos meses você antecipou.",
    prazoRestante:
      "Quantos meses ainda faltam segundo o contrato atual. É este valor — e não o prazo original — que entra no cálculo da prestação e da amortização.",
    taxaNominal:
      "Taxa de juros anual do contrato, em fração: digite 0,1002 para 10,02% a.a. É dividida por 12 (proporcionalidade simples) para obter a taxa mensal aplicada em todos os meses.",
    taxaEfetiva:
      "Taxa efetiva anual que aparece no contrato, em fração como a nominal: 0,1049 para 10,49% a.a. Serve apenas para conferência — ela deve ficar próxima de (1 + nominal ÷ 12)¹² − 1. Não entra em nenhum cálculo da simulação.",
    indexador:
      "Índice que corrige o saldo devedor todo mês. TR é o padrão do SFH; poupança é uma alternativa de mercado usada em alguns contratos. O simulador trata os dois do mesmo jeito: um cenário de taxa anual constante, convertido para taxa mensal por juros compostos — não reproduz a regra oficial da poupança (que muda com a Selic), apenas aproxima seu efeito.",
    cenarioIndexador:
      "O indexador escolhido corrige o saldo devedor todo mês. Como ninguém sabe a taxa futura, você escolhe um cenário anual constante, convertido para taxa mensal por juros compostos. Indexador e juros nunca são somados numa taxa só: aparecem em colunas separadas na tabela mensal.",
    indexadorPersonalizado:
      "Taxa anual do indexador em fração: 0,02 para 2% a.a. Use 0 para simular sem nenhuma correção monetária do saldo.",
    segurosTarifas:
      "Valor fixo somado a toda prestação (seguros MIP e DFI, tarifa de administração). Entra na prestação total e no limite de prestação, mas nunca abate o saldo nem rende juros.",
    limiteSaldo:
      "Serve só de alerta: se o saldo devedor projetado passar deste valor em algum mês, o mês é destacado na tabela e o resumo aponta “Ultrapassado”. Não altera nenhum cálculo.",
    limitePrestacao:
      "Mesmo princípio do limite de saldo, aplicado à prestação total (já com seguros e tarifas). Útil para ver se a parcela caberia no seu orçamento em todos os meses.",
  };
</script>

<section class="secao secao-importar">
  <div class="cabecalho-importar">
    <div>
      <h3>Importar do extrato</h3>
      <p class="descricao-importar">
        Envie o PDF do extrato do banco para preencher automaticamente os campos que ele conseguir
        reconhecer. Confira os valores antes de simular.
      </p>
    </div>
    <label class="botao-importar" class:desabilitado={importando}>
      {importando ? "Lendo PDF..." : "Selecionar PDF"}
      <input
        type="file"
        accept="application/pdf"
        on:change={aoSelecionarArquivo}
        disabled={importando}
        hidden
      />
    </label>
  </div>
  {#if mensagemImportacao}
    <p class="mensagem-importacao">{mensagemImportacao}</p>
  {/if}
  {#if erroImportacao}
    <p class="erro-importacao">{erroImportacao}</p>
  {/if}
</section>

<section class="secao">
  <h3>Dados do contrato</h3>
  <div class="grade">
    <label>
      <span class="rotulo-linha">
        Data-base
        <Ajuda rotulo="a data-base" texto={textos.dataBase} />
      </span>
      <input type="date" bind:value={contrato.data_base} class:invalido={camposFaltando.has("data_base")} />
    </label>
    <label>
      <span class="rotulo-linha">
        Saldo devedor (R$)
        <Ajuda rotulo="o saldo devedor" texto={textos.saldoDevedor} />
      </span>
      <input
        type="number"
        step="0.01"
        bind:value={contrato.saldo_devedor}
        class:invalido={camposFaltando.has("saldo_devedor")}
      />
    </label>
    <label>
      <span class="rotulo-linha">
        Prazo original (meses)
        <Ajuda rotulo="o prazo original" texto={textos.prazoOriginal} />
      </span>
      <input
        type="number"
        bind:value={contrato.prazo_original}
        class:invalido={camposFaltando.has("prazo_original")}
      />
    </label>
    <label>
      <span class="rotulo-linha">
        Prazo restante (meses)
        <Ajuda rotulo="o prazo restante" texto={textos.prazoRestante} />
      </span>
      <input
        type="number"
        bind:value={contrato.prazo_restante}
        class:invalido={camposFaltando.has("prazo_restante")}
      />
    </label>
    <label class="largura-total">
      <span class="rotulo-linha">
        Sistema de amortização
        <Ajuda
          rotulo="o sistema de amortização"
          texto={explicacaoSistema[contrato.sistema_amortizacao]}
        />
      </span>
      <select bind:value={contrato.sistema_amortizacao}>
        {#each sistemas as s}
          <option value={s.valor}>{s.rotulo}</option>
        {/each}
      </select>
    </label>
  </div>
</section>

<section class="secao">
  <h3>Taxas e indexador</h3>
  <div class="grade">
    <label>
      <span class="rotulo-linha">
        Taxa nominal anual (fração)
        <Ajuda rotulo="a taxa nominal anual" texto={textos.taxaNominal} />
      </span>
      <input
        type="number"
        step="0.0001"
        bind:value={contrato.taxa_nominal_anual}
        class:invalido={camposFaltando.has("taxa_nominal_anual")}
      />
    </label>
    <label>
      <span class="rotulo-linha">
        Taxa efetiva informada (fração)
        <Ajuda rotulo="a taxa efetiva informada" texto={textos.taxaEfetiva} />
      </span>
      <input
        type="number"
        step="0.0001"
        bind:value={contrato.taxa_efetiva_informada}
        class:invalido={camposFaltando.has("taxa_efetiva_informada")}
      />
    </label>
    <label>
      <span class="rotulo-linha">
        Indexador
        <Ajuda rotulo="o indexador" texto={textos.indexador} />
      </span>
      <select bind:value={contrato.indexador}>
        {#each indexadores as i}
          <option value={i.valor}>{i.rotulo}</option>
        {/each}
      </select>
    </label>
    <label>
      <span class="rotulo-linha">
        Cenário de {ROTULO_INDEXADOR[contrato.indexador]}
        <Ajuda rotulo="o cenário do indexador" texto={textos.cenarioIndexador} />
      </span>
      <select bind:value={cenarioNome}>
        {#each cenarios as c}
          <option value={c.nome}>{c.nome}</option>
        {/each}
      </select>
    </label>
    {#if cenarioNome === "Personalizada"}
      <label>
        <span class="rotulo-linha">
          {ROTULO_INDEXADOR[contrato.indexador]} anual personalizada (fração)
          <Ajuda rotulo="a taxa personalizada" texto={textos.indexadorPersonalizado} />
        </span>
        <input
          type="number"
          step="0.0001"
          bind:value={taxaIndexadorPersonalizada}
          class:invalido={indexadorPersonalizadaFaltando}
        />
      </label>
    {/if}
  </div>
</section>

<section class="secao">
  <h3>Seguros e tarifas</h3>
  <div class="grade">
    <label>
      <span class="rotulo-linha">
        Seguros e tarifas mensais (R$)
        <Ajuda rotulo="seguros e tarifas mensais" texto={textos.segurosTarifas} />
      </span>
      <input
        type="number"
        step="0.01"
        bind:value={contrato.seguros_tarifas_mensais}
        class:invalido={camposFaltando.has("seguros_tarifas_mensais")}
      />
    </label>
  </div>
</section>

<section class="secao">
  <h3>Limites financeiros</h3>
  <div class="grade">
    <label>
      <span class="rotulo-linha">
        Limite do saldo devedor (R$)
        <Ajuda rotulo="o limite de saldo devedor" texto={textos.limiteSaldo} />
      </span>
      <input
        type="number"
        step="0.01"
        bind:value={contrato.limite_saldo}
        class:invalido={camposFaltando.has("limite_saldo")}
      />
    </label>
    <label>
      <span class="rotulo-linha">
        Limite da prestação total (R$)
        <Ajuda rotulo="o limite de prestação total" texto={textos.limitePrestacao} />
      </span>
      <input
        type="number"
        step="0.01"
        bind:value={contrato.limite_prestacao}
        class:invalido={camposFaltando.has("limite_prestacao")}
      />
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
  .rotulo-linha {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }
  .largura-total {
    grid-column: 1 / -1;
  }
  .cabecalho-importar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .descricao-importar {
    margin: 0.3rem 0 0 0;
    font-size: 0.82rem;
    color: var(--cor-texto-secundario);
    max-width: 46ch;
  }
  .botao-importar {
    background: var(--cor-destaque);
    color: white;
    border: none;
    padding: 0.6rem 1.3rem;
    border-radius: var(--raio-sm);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s ease;
  }
  .botao-importar:hover {
    background: var(--cor-destaque-hover);
  }
  .botao-importar.desabilitado {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .mensagem-importacao {
    margin: 0.9rem 0 0 0;
    font-size: 0.82rem;
    color: var(--cor-destaque);
  }
  .erro-importacao {
    margin: 0.9rem 0 0 0;
    font-size: 0.82rem;
    color: #a12020;
    background: var(--cor-perigo-fundo);
    padding: 0.6rem 0.8rem;
    border-radius: var(--raio-sm);
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
  input.invalido {
    border-color: var(--cor-perigo);
    background: var(--cor-perigo-fundo);
  }
  input.invalido:focus {
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15);
  }
</style>
