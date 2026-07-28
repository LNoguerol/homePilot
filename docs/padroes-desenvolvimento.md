# Padrões de desenvolvimento

Convenções a seguir ao adicionar ou alterar código no HomePilot, extraídas do que já foi estabelecido no motor financeiro e na API. Servem para manter consistência à medida que o projeto cresce (banco, autenticação, novas funcionalidades).

## Idioma

Todo identificador, comentário, docstring, mensagem de erro e texto de UI é escrito em **português**. Exceções só quando há um contrato externo explícito (ex.: os paths HTTP `/api/health`, `/api/simulations` vieram assim da especificação original) — e mesmo assim, a exceção deve ser justificada em comentário ou documentação, não silenciosa.

## Backend (Python)

- **`Decimal`, nunca `float`**, para qualquer valor monetário ou taxa. Arredondamento explícito a centavos (`ROUND_HALF_UP`) em cada etapa intermediária do cálculo, não só no resultado final — evita divergência de arredondamento acumulada.
- **Motor financeiro (`core/`) desacoplado de framework.** Nada em `core/` importa FastAPI ou Pydantic — só `dataclasses`, `enum`, `decimal`, `datetime` e stdlib. A camada `esquemas/` é a única ponte entre Pydantic (API) e dataclasses (domínio). Ao adicionar uma nova camada com estado (ex. banco de dados), seguir o mesmo princípio: modelos ORM ficam isolados em `bd/`, sem vazar para `core/`.
- **Erros de negócio vs. erros de argumento.** Uma condição que pode legitimamente acontecer vinda de uma requisição de usuário (saldo inválido, e-mail duplicado, prestação insuficiente) é um erro de **negócio**: levanta uma exceção de domínio dedicada (`ErroSimulacaoInvalida`, e futuramente algo como `ErroCadastroInvalido`), mapeada por um `@app.exception_handler` para um código HTTP apropriado (422, 409, 401) com mensagem em português. Uma condição que só ocorreria por bug de programação (ex. `prazo_meses <= 0` passado direto para uma função interna já protegida pela validação da API) pode continuar como `ValueError`/`AssertionError` comuns.
- **Validação em funções dedicadas e explícitas** (`validar_contrato`, `validar_amortizacoes`, `validar_taxa_tr`), não espalhada inline pelo meio do cálculo — cada uma levanta mensagens específicas e compreensíveis para o usuário final, nunca uma mensagem genérica de exceção Python.
- **Constantes de limite nomeadas e comentadas** no topo do módulo (`LIMITE_MESES_SEGURANCA`, `LIMITE_TAXA_ANUAL_RAZOAVEL` etc.), não números soltos no meio da lógica.
- **Docstring de módulo quando a lógica não é óbvia.** `simulador.py` e `taxas.py` têm docstrings de módulo explicando o *porquê* de uma convenção (ex.: por que recalcular a prestação todo mês, por que taxa nominal e não efetiva) — isso é obrigatório para decisões não óbvias, não para código autoexplicativo.
- **Sem comentário para o que já está claro pelo nome.** Comentário só quando explica uma decisão, um caso de borda ou uma armadilha — nunca repete o que o código já diz.

## Testes

- Todo módulo de `core/` tem teste correspondente em `backend/tests/`. Testes cobrem: fórmula isolada (ex. um cálculo manual verificável da Tabela Price), casos de borda (taxa zero, quitação antecipada, saldo nunca negativo) e o fluxo de API (`test_api.py`, via `TestClient`).
- Ao escrever um teste, preferir um contrato pequeno e dedicado quando o cenário completo do README não serve para a asserção (ex.: os testes de "sem alerta" usam um contrato pequeno próprio, porque o contrato padrão de 376 meses legitimamente ultrapassa os limites sem amortização extra — isso é comportamento correto do motor, não circunstância a ser mascarada).
- Não escrever teste para caminho matematicamente inalcançável através do fluxo público (`simular()`) só para "cobrir a linha" — testar a função interna diretamente com uma combinação de parâmetros que force o caso, e documentar por que o caminho público não alcança essa condição.
- Rodar `pytest -q` antes de considerar qualquer mudança em `core/` ou `api/` concluída.

## Frontend (Svelte + TS)

- **Nenhum cálculo financeiro no frontend.** Componentes só formatam (`moeda.ts`) e exibem o que a API já devolveu pronto.
- Um componente por responsabilidade visual (`CartoesResumo`, `GraficoSaldo`, `TabelaCronograma` etc.) — evitar componentes que misturam orquestração de estado com apresentação; orquestração fica em `App.svelte`.
- Tipos TS em `tipos.ts` espelham exatamente os schemas Pydantic da API (inclusive campos monetários como `string`, já que vêm serializados como texto para preservar precisão decimal).

## Git

- Nunca commitar sem pedido explícito do usuário (ver `CLAUDE.md`).
- Mensagens de commit descrevem o *porquê*, não só o *o quê*.

## Documentação

- Toda decisão de arquitetura ou de regra financeira não óbvia pelo código vai em `docs/`, não em comentário espalhado. Ao adicionar um documento novo em `docs/`, referenciá-lo em [`roadmap.md`](roadmap.md) e, se relevante, em `CLAUDE.md`.
- Documento de desenho (ainda não implementado) começa com um aviso de status explícito no topo — ver `banco.md`/`autenticacao.md` como exemplo — para nunca ser confundido com o estado atual do código.
