# HomePilot

Simulação e planejamento de financiamentos imobiliários brasileiros (Tabela Price ou SAC + TR + amortizações extraordinárias).

> **Aviso:** Este projeto é uma ferramenta educacional e de planejamento. Os resultados são estimativas e não substituem o demonstrativo oficial da instituição financeira, orientação jurídica, contábil ou financeira.

## 1. Objetivo

Permitir simular um financiamento pela Tabela Price ou pelo SAC, com correção do saldo pela TR, aplicar amortizações extraordinárias (ex.: FGTS) por redução de prazo ou de prestação, e acompanhar se o saldo devedor e a prestação total respeitam limites configuráveis (padrão: R$ 350.000,00 e R$ 3.800,00).

## 2. Arquitetura

Monorepo com backend e frontend desacoplados:

```
backend/   API FastAPI + motor financeiro (Python, Decimal)
frontend/  SPA em Svelte + TypeScript + Vite + Chart.js
outputs/   destino sugerido para CSVs exportados manualmente
```

Todo o código (identificadores, comentários, mensagens e textos de interface) foi escrito em português. Os caminhos dos endpoints HTTP (`/api/health`, `/api/simulations`, `/api/simulations/compare`) foram mantidos em inglês por serem contrato explícito da especificação do projeto.

O motor financeiro (`backend/src/homepilot/core/`) é desacoplado da API: usa apenas `dataclasses` e `Decimal`, sem depender de FastAPI/Pydantic. A camada `backend/src/homepilot/esquemas/` converte entre os modelos Pydantic da API e os modelos de domínio. **O frontend nunca calcula nada financeiro** — apenas envia dados e exibe o que o backend retorna.

```
backend/src/homepilot/
├── main.py                 API FastAPI, CORS, tratamento de erros
├── api/simulacoes.py        endpoints /api/simulations e /compare
├── api/auth.py               endpoints /api/auth/cadastro, /login, /eu
├── esquemas/simulacao.py    Pydantic + conversão para o domínio
├── esquemas/auth.py          Pydantic de cadastro/login
├── auth/                     hash de senha, JWT, dependency de rota protegida
├── bd/                       conexão SQLAlchemy + modelo ORM (MariaDB)
└── core/
    ├── modelos.py           dataclasses de domínio
    ├── taxas.py              conversões de taxa anual -> mensal
    ├── tabela_price.py       fórmulas da Tabela Price
    ├── tabela_sac.py         fórmulas do SAC
    ├── simulador.py          laço mensal de simulação
    └── resumos.py            indicadores agregados

backend/migrations/          migrations do Alembic (schema do MariaDB)

frontend/src/
├── App.svelte                orquestra estado, autenticação e chamadas à API
└── lib/
    ├── api.ts, autenticacao.ts, tipos.ts, moeda.ts, csv.ts
    └── componentes/
        FormularioContrato, AmortizacoesExtras, CartoesResumo,
        GraficoSaldo, GraficoPrestacao, GraficoComposicao,
        TabelaCronograma, ComparacaoCenarios, TelaLogin, TelaCadastro,
        Ajuda, Logo
```

Ver [`docs/arquitetura.md`](docs/arquitetura.md), [`docs/banco.md`](docs/banco.md) e [`docs/autenticacao.md`](docs/autenticacao.md) para o detalhamento de cada camada.

## 3. Instalação e execução

### Sem Docker

**Banco de dados** (MariaDB — necessário para cadastro/login; ver [`docs/banco.md`](docs/banco.md)):

Se você já tem um MariaDB/MySQL instalado na máquina (porta 3306 ocupada), use-o diretamente: crie o banco e o usuário à mão e aponte `HOMEPILOT_DB_*` para ele (ver variáveis abaixo) — não precisa do serviço `banco` do Docker Compose.

Caso prefira o MariaDB via Docker mesmo com um já instalado localmente, o serviço `banco` do `docker-compose.yml` expõe a porta **3307** no host (em vez de 3306) exatamente para não conflitar com uma instalação local:

```bash
docker compose up banco -d   # MariaDB acessível em localhost:3307
export HOMEPILOT_DB_PORT=3307
```

**Backend** (Python 3.11+):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head           # cria a tabela usuarios no MariaDB
uvicorn homepilot.main:app --reload --port 8000
```

Variáveis de ambiente do banco e seus padrões: `HOMEPILOT_DB_HOST=localhost`, `HOMEPILOT_DB_PORT=3306` (mude para `3307` se estiver usando o serviço `banco` do Docker Compose — ver acima), `HOMEPILOT_DB_NOME=homepilot`, `HOMEPILOT_DB_USUARIO=homepilot`, `HOMEPILOT_DB_SENHA=homepilot`, `HOMEPILOT_JWT_SECRET` (tem um valor padrão de desenvolvimento — trocar antes de qualquer uso real).

Testes do backend (usam SQLite local automaticamente — não exigem o MariaDB rodando):

```bash
cd backend && source .venv/bin/activate && pytest -q
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> http://localhost:8000)
npm run build       # build de produção em frontend/dist
```

Abra `http://localhost:5173` com o backend já rodando na porta 8000.

### Com Docker

```bash
docker compose up
```

Sobe backend em `http://localhost:8000` e frontend em `http://localhost:5173`.

## 4. Premissas e fórmulas

### 4.1 Taxa de juros mensal

A taxa **nominal** anual do contrato é convertida para taxa mensal por proporcionalidade simples:

```
taxa_mensal_juros = taxa_nominal_anual / 12
```

A taxa **efetiva** informada no contrato é apenas uma referência de conferência: ela corresponde ao efeito composto de 12 aplicações da taxa mensal nominal, `(1 + taxa_nominal_anual/12)^12 - 1`. Para o cenário inicial (10,02% a.a. nominal), esse cálculo dá ≈ 10,4932% a.a., que bate com os 10,49% informados no contrato — confirmando a convenção adotada. A taxa efetiva **não** é usada em nenhum cálculo mensal.

### 4.2 TR (e demais indexadores)

Conversão por juros compostos, conforme pedido na especificação:

```
taxa_mensal_tr = (1 + taxa_anual)^(1/12) - 1
```

TR e taxa de juros contratual **nunca são somadas em uma única taxa**: o cronograma mostra a correção pela TR e os juros como colunas separadas.

### 4.3 Tabela Price

```
PMT = PV × [i × (1+i)^n] / [(1+i)^n - 1]
```

`PV` é o saldo corrigido do mês, `i` é `taxa_mensal_juros`, `n` é o prazo restante. Quando `i = 0`, `PMT = PV / n`.

**Importante:** a prestação financeira é recalculada todo mês com base no saldo já corrigido pela TR e no prazo restante vigente (em vez de fixada uma única vez no início). É essa recorrência que faz a prestação acompanhar a evolução da TR ao longo do contrato — como ocorre na prática em financiamentos SFH indexados à TR — e, como consequência natural, quando resta exatamente 1 mês de prazo a própria fórmula devolve o valor exato para zerar o saldo (saldo corrigido + juros), resolvendo o ajuste da última parcela sem necessidade de um caso especial no código.

### 4.4 SAC (Sistema de Amortização Constante)

Alternativa à Tabela Price, escolhida no campo `sistema_amortizacao` do contrato (`"price"`, padrão, ou `"sac"`). No SAC a grandeza constante é a **amortização**, não a prestação:

```
A   = PV / n
PMT = A + juros
```

`PV` é o saldo corrigido do mês e `n` o prazo restante. Como a fatia amortizada é sempre a mesma e os juros incidem sobre um saldo que cai mais rápido, a prestação é **decrescente**: começa mais alta que na Price e termina bem mais baixa, com um total de juros significativamente menor.

Comparação para o cenário inicial do projeto (R$ 332.786,77 / 376 meses / 10,02% a.a. nominal / TR 1,5% a.a.):

| | Price | SAC |
|---|---|---|
| Prestação financeira no 1º mês | R$ 2.909,87 | R$ 3.668,39 |
| Prestação financeira no último mês | R$ 4.633,79 | R$ 1.422,95 |
| Total de juros | R$ 923.335,64 | R$ 616.229,62 |

Note o efeito colateral que o simulador expõe na Price indexada à TR: no início a amortização (R$ 127,65 no 1º mês) é menor que a correção monetária, então o **saldo devedor cresce** nos primeiros anos. No SAC isso não acontece — a amortização de R$ 886,17 já supera a correção desde o 1º mês.

Como na Price, a fórmula é reaplicada a cada mês sobre o saldo corrigido e o prazo restante vigentes; quando resta 1 mês, `A = PV / 1` zera o saldo exatamente, dispensando um caso especial para a última parcela.

### 4.5 Amortização extraordinária — redução de prazo

No mês do evento: aplica-se o valor extra ao saldo (nunca deixando saldo negativo — o valor é limitado ao saldo disponível) e recalcula-se o prazo preservando a grandeza característica do sistema. Na **Price**, mantém-se a prestação financeira já calculada naquele mês e isola-se `n` na fórmula:

```
n = -ln(1 - i × saldo_novo / prestacao) / ln(1 + i)
```

arredondado para cima (número inteiro de meses). Quando `i = 0`, `n = saldo_novo / prestacao`.

No **SAC**, mantém-se a amortização mensal daquele mês e a relação é sempre linear:

```
n = saldo_novo / amortizacao
```

Em ambos os casos o efeito é o mesmo: a parcela segue no patamar em que estava e a quitação é antecipada. Se o saldo zerar, a simulação encerra naquele mês.

### 4.6 Amortização extraordinária — redução de prestação

Mantém-se o prazo restante; reduz-se o saldo; a prestação financeira do mês seguinte é automaticamente recalculada pelo sistema do contrato com o novo saldo e o mesmo prazo.

### 4.7 Sequência mensal de cálculo

1. Saldo inicial do mês.
2. Correção monetária pela TR.
3. Saldo corrigido.
4. Juros sobre o saldo corrigido.
5. Prestação financeira e amortização ordinária pelo sistema do contrato (saldo corrigido e prazo restante vigentes): na Price calcula-se a prestação e a amortização é o resíduo; no SAC calcula-se a amortização e a prestação é a soma com os juros.
7. Aplicação da amortização ordinária.
8. Aplicação de eventual amortização extraordinária do mês.
9. Recálculo do prazo ou da prestação, conforme a estratégia.
10. Soma de seguros e tarifas para obter a prestação total.
11. Registro do saldo final.

### 4.8 Arredondamento

Todos os valores monetários são arredondados para centavos (`ROUND_HALF_UP`) a cada etapa, usando `Decimal` em todo o motor financeiro — nunca `float`.

## 5. Limitações e possíveis diferenças em relação ao Bradesco (ou qualquer banco)

Esta é uma **convenção simplificada**, não uma reprodução do extrato oficial de nenhuma instituição. Podem gerar diferenças em relação ao extrato real:

- a ordem operacional interna do banco entre correção, juros e amortização;
- a data de aniversário contratual (o HomePilot usa sempre o dia da data-base, com ajuste automático para meses mais curtos);
- os critérios de arredondamento em cada etapa;
- a política interna de seguros e tarifas (aqui tratados como valor fixo mensal);
- o índice de TR real divulgado pelo Banco Central mês a mês (aqui, cenários de TR anual constante, convertidos para uma taxa mensal equivalente fixa — a estrutura já está preparada para futuramente aceitar uma série histórica mensal de TR);
- o número de meses recalculado após uma amortização com redução de prazo assume taxa de juros constante e desconhece futuras correções de TR; a cada mês o prazo e a prestação são recalculados novamente com o saldo efetivamente atualizado.
- as regras de datas e periodicidade do FGTS são tratadas apenas como parâmetros configuráveis pelo usuário, não como regras legais permanentes.

## 6. Entendendo os campos na tela

Todo campo do formulário e todo indicador do resumo têm um botão discreto **?** alinhado à direita do rótulo. Clicar abre um balão explicando o que o campo significa, em que unidade preencher e se ele afeta ou não o cálculo — por exemplo, que a taxa efetiva serve só de conferência, que o prazo original não entra em nenhuma fórmula, e que os limites financeiros apenas disparam alertas.

Por isso os rótulos são curtos e trazem apenas a unidade (`(R$)`, `(meses)`, `(fração)`): os exemplos de preenchimento ficam no balão, não no rótulo, para a linha não acumular parênteses e botão ao mesmo tempo.

O balão abre por clique (não por passar o mouse), para funcionar igual no celular e por teclado. Fecha ao clicar fora, ao apertar `Esc` ou ao abrir a explicação de outro campo.

## 7. Como escolher o sistema de amortização

Na seção "Dados do contrato" do formulário, o campo **Sistema de amortização** alterna entre **Price** (prestação constante, padrão) e **SAC** (amortização constante, prestação decrescente). Na interface os dois aparecem sem o prefixo "Tabela", para que as duas opções fiquem simétricas; nesta documentação "Tabela Price" continua sendo usado como termo formal. O botão **?** do campo explica a opção selecionada no momento. A escolha vale para a simulação e também para a comparação de cenários de TR — para comparar Price contra SAC, simule uma vez em cada sistema. Ver §4.3 e §4.4 para as fórmulas.

## 8. Como cadastrar amortizações extraordinárias

A seção "Amortizações extraordinárias" tem dois blocos, porque são duas coisas diferentes: um compromisso contínuo e eventos avulsos.

**Aporte recorrente** — marque a caixa para ativar e informe valor, periodicidade em meses, mês inicial e até quando (**quitar o financiamento** ou **um mês específico**), mais a estratégia. Serve para o caso mais comum de quem quer antecipar: "R$ 500 a mais todo mês". Um resumo abaixo dos campos mostra quantos aportes e o total, quando há mês final definido; sem mês final o total só é conhecido depois de simular, e a linha diz isso em vez de estimar.

Com periodicidade **24**, o bloco recorrente reproduz exatamente o saque bienal do FGTS — o resultado é idêntico a cadastrar os cinco eventos um a um.

**Aportes pontuais** — para o que não é regular: **Adicionar** cria uma linha (data, valor, estratégia), **✕** remove uma linha e **Limpar todos** esvazia a lista. O cenário inicial já vem com os cinco aportes de R$ 40.000,00 (junho de 2027, 2029, 2031, 2033 e 2035), todos com redução de prazo.

Os dois blocos convivem: num mês em que o recorrente e um pontual coincidem, **os valores somam** (ver [`docs/regras-financeiras.md`](docs/regras-financeiras.md) §4.0).

## 9. Como comparar cenários

Na seção "Comparação de cenários de TR", o botão **Comparar cenários** executa simultaneamente os quatro cenários padrão (TR 0%, 1,5%, 2,0% e 2,5% a.a.) com os mesmos dados de contrato e amortizações, exibindo quitação estimada, maior saldo, maior prestação, juros totais, total de correção pela TR e se os limites foram respeitados em cada cenário.

## 10. Exportação de CSV

O botão **Exportar CSV** (na tabela mensal) gera o cronograma completo com separador `;`, decimal com vírgula, codificação UTF-8 com BOM e nomes de colunas em português — pronto para abrir no Excel/LibreOffice sem problemas de acentuação.

## 11. Como executar os testes

```bash
cd backend
source .venv/bin/activate
pytest -q
```

80 testes cobrindo: cálculo da prestação Price e da amortização do SAC (ambos com um caso de cálculo manual verificável), conversão de taxa anual para mensal (nominal e TR), saldo nunca negativo, amortização extraordinária nos dois sistemas, redução de prazo, redução de prestação, quitação antecipada, ajuste da última parcela, perfil decrescente da prestação no SAC e seu menor custo total de juros, alertas de saldo e de prestação, aporte recorrente (mensal, com fim definido, equivalência com os eventos de FGTS, soma com aportes pontuais na mesma competência), comparação de cenários, validações da API e cadastro/login (ver [`docs/autenticacao.md`](docs/autenticacao.md)).

## 12. Endpoints da API

- `GET /api/health` → `{"status": "ok"}`
- `POST /api/simulations` → recebe contrato, cenário de TR, amortizações pontuais e (opcional) `aporte_recorrente`; devolve cronograma mensal e resumo.
- `POST /api/simulations/compare` → recebe contrato, amortizações pontuais, (opcional) `aporte_recorrente` e uma lista de cenários de TR; devolve o resumo de cada cenário.
- `POST /api/auth/cadastro` → cria uma conta (nome, e-mail, senha, telefone opcional, cidade, estado). Retorna 409 se o e-mail já existir.
- `POST /api/auth/login` → recebe e-mail e senha, devolve `{"token": "...", "tipo": "bearer"}` (JWT). Retorna 401 se as credenciais forem inválidas.
- `GET /api/auth/eu` → devolve os dados do usuário autenticado (requer `Authorization: Bearer <token>`).

Validações com mensagens em português retornam HTTP 422: saldo inválido, prazo ≤ 0, taxa negativa, amortização negativa, amortização com data anterior à data-base, prestação insuficiente para pagar os juros, valores fora de faixas razoáveis, aporte recorrente com valor ≤ 0 / periodicidade < 1 / mês inicial anterior à data-base / mês final anterior ao inicial, senha de cadastro menor que 8 caracteres.
