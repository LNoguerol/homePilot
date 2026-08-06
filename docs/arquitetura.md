# Arquitetura

Este documento descreve como o HomePilot é organizado internamente e por quê. Para instruções de instalação, fórmulas financeiras e limitações, ver `README.md`.

## Visão geral

Monorepo com dois módulos independentes que só se comunicam via HTTP:

```
backend/   API FastAPI + motor financeiro (Python, Decimal)
frontend/  SPA em Svelte + TypeScript + Vite + Chart.js
outputs/   destino sugerido para CSVs exportados manualmente
```

O frontend nunca calcula nada financeiro — apenas envia os dados do formulário e renderiza o que o backend devolve. Toda a matemática (Tabela Price, SAC, TR, amortizações, alertas) vive no backend.

## Backend

### Camadas

```
backend/src/homepilot/
├── main.py                  app FastAPI, CORS, tratamento global de erros
├── api/
│   └── simulacoes.py        endpoints HTTP (/api/simulations, /compare)
├── esquemas/
│   └── simulacao.py         Pydantic (entrada/saída da API) + conversão para o domínio
└── core/                    motor financeiro puro
    ├── modelos.py           dataclasses de domínio (sem Pydantic/FastAPI)
    ├── excecoes.py           ErroSimulacaoInvalida
    ├── taxas.py              conversões de taxa anual -> mensal
    ├── tabela_price.py       fórmulas da Tabela Price
    ├── tabela_sac.py         fórmulas do SAC
    ├── simulador.py          laço mensal de simulação (validação + cálculo)
    └── resumos.py            indicadores agregados (maior saldo, alertas, etc.)
```

A regra central é a **separação entre `core/` e o resto**: `core/` usa apenas `dataclasses` e `Decimal` da stdlib, sem nenhuma dependência de FastAPI ou Pydantic. Isso permite testar o motor financeiro isoladamente (`backend/tests/test_simulador.py`, `test_tabela_price.py`, `test_taxas.py`, `test_extra_payments.py`) sem subir uma aplicação web, e mantém a possibilidade de reaproveitar o motor em outro contexto (CLI, job em lote, outra API) sem alterações.

`esquemas/simulacao.py` é a única camada que conhece os dois lados: valida a entrada HTTP com Pydantic e converte para os dataclasses de `core/modelos.py` antes de chamar o motor; faz o caminho inverso para montar a resposta.

### Tratamento de erros

Erros de regra de negócio (saldo inválido, prazo ≤ 0, taxa negativa, prestação insuficiente para pagar os juros, valores fora de faixas razoáveis) são sinalizados no `core/` via a exceção `ErroSimulacaoInvalida` (definida em `core/excecoes.py`). O `main.py` registra um `@app.exception_handler(ErroSimulacaoInvalida)` que converte isso em HTTP 422 com mensagem em português. Erros de argumento puramente estrutural (ex.: `prazo_meses <= 0` passado diretamente para `tabela_price.calcular_prestacao`) continuam como `ValueError` comum, pois não deveriam ocorrer vindos da API (já filtrados pelo Pydantic).

### Fluxo de uma simulação

1. `POST /api/simulations` recebe `ContratoEntrada` + `CenarioIndexadorEntrada` + lista de `AmortizacaoEntrada` (Pydantic).
2. `esquemas/simulacao.py` converte para `DadosContrato`, `CenarioIndexador`, `list[AmortizacaoExtraordinaria]` (dataclasses).
3. `core/simulador.simular(...)` valida o contrato e roda o laço mensal descrito no README (seção 4.6), produzindo uma lista de `ParcelaMensal`.
4. `core/resumos.montar_resumo(...)` agrega os indicadores (`ResumoSimulacao`): maior saldo, maior prestação, totais de juros/indexador/seguros, mês de quitação, alertas de limite.
5. `esquemas/simulacao.py` converte `ResultadoSimulacao` de volta para `SimulacaoSaida` (Pydantic) e a API devolve JSON.

`POST /api/simulations/compare` repete esse fluxo para os quatro cenários padrão do indexador escolhido (`CENARIOS_PADRAO_POR_INDEXADOR` em `core/taxas.py`), reaproveitando o mesmo contrato e amortizações, e devolve só os resumos de cada cenário.

## Frontend

```
frontend/src/
├── App.svelte                orquestra estado e chamadas à API
└── lib/
    ├── api.ts                 chamadas fetch para o backend (simular, compararCenarios)
    ├── tipos.ts                interfaces TS espelhando os schemas Pydantic
    ├── moeda.ts                formatação de moeda/data em pt-BR
    ├── csv.ts                  exportação de cronograma para CSV (client-side)
    └── componentes/
        FormularioContrato.svelte    dados do contrato
        AmortizacoesExtras.svelte     listas editáveis de aportes recorrentes e pontuais
        CartoesResumo.svelte          indicadores agregados
        GraficoSaldo.svelte           evolução do saldo devedor
        GraficoPrestacao.svelte       evolução da prestação
        GraficoComposicao.svelte      composição acumulada (juros/amortização/TR)
        TabelaCronograma.svelte       cronograma mês a mês + exportar CSV
        ComparacaoCenarios.svelte     resultado da comparação de cenários de TR
        TelaLogin.svelte              formulário de login
        TelaCadastro.svelte           formulário de cadastro
        Ajuda.svelte                  botão "?" com a explicação de um campo
        Logo.svelte                   marca do HomePilot em SVG
```

`App.svelte` mantém o estado do contrato e das amortizações (com os valores do cenário inicial da especificação como default), chama `api.ts` ao simular/comparar, e distribui o resultado para os componentes de exibição. Nenhum componente recalcula valores financeiros — apenas formata (`moeda.ts`) e exporta (`csv.ts`) o que já veio pronto do backend.

### Textos de ajuda dos campos

`Ajuda.svelte` é o único componente de ajuda: recebe `texto` e `rotulo` e renderiza um botão "?" discreto que abre um balão. Abre por **clique** (não por hover) para funcionar em toque e por teclado, e fecha ao clicar fora, ao apertar Esc ou ao abrir o balão de outro campo.

Duas decisões de posicionamento que não são óbvias no código:

- O rótulo é um **flex de linha única** (`.rotulo-linha` / `.rotulo`) com `gap` fixo, e o componente tem `flex: none`. É o flex que impede o gatilho de cair sozinho para a linha de baixo quando o rótulo é longo — o texto quebra internamente e o "?" continua ao lado dele. Já foi tentado `justify-content: space-between` (gatilho colado na borda direita do campo): alinha bem em coluna, mas afasta o "?" do rótulo e quebra a associação visual — não repetir.
- O lado de crescimento do balão é decidido na abertura via `getBoundingClientRect()`, testando **os dois lados**: o padrão é crescer para a direita, e só vira quando não couber ali *e* couber virado.

Por consequência dessa ancoragem, os rótulos devem ser curtos e conter apenas a unidade (`(R$)`, `(meses)`, `(fração)`). Exemplos de preenchimento vão no `texto` do balão — repetir "(fração, ex.: 0,1002 = 10,02%)" no rótulo *e* oferecer o "?" polui a linha e foi o que motivou o encurtamento.

Os textos ficam num objeto `textos` no `<script>` de cada componente que tem campos (`FormularioContrato`, `AmortizacoesExtras`, `CartoesResumo`), não dentro do `Ajuda`. A explicação do sistema de amortização é a única dinâmica: muda conforme a opção selecionada. Ao alterar uma regra financeira, revisar esses objetos — eles são a única fonte de explicação que o usuário final lê, já que `regras-financeiras.md` é documento interno.

Em desenvolvimento, o Vite faz proxy de `/api` para o backend (`http://localhost:8000` por padrão, ou `VITE_API_PROXY_TARGET` quando rodando via Docker Compose, apontando para `http://backend:8000`).

## Docker

`docker-compose.yml` sobe dois serviços (`backend`, `frontend`) a partir de imagens genéricas (`python:3.12-slim`, `node:20-slim`) com bind mount do código-fonte e instalação/execução inline — sem Dockerfiles dedicados, por simplicidade neste estágio do projeto. `frontend` depende de `backend` e recebe `VITE_API_PROXY_TARGET=http://backend:8000` para o proxy funcionar dentro da rede do Compose.
