# HomePilot

Simulador de financiamento imobiliário brasileiro (Tabela Price ou SAC + TR + amortizações extraordinárias). Ver `README.md` para arquitetura completa, fórmulas e instruções de instalação — este arquivo cobre apenas convenções e contexto que não estão lá.

## Convenção de idioma

Todo o código (identificadores, comentários, mensagens, textos de UI) deve ser escrito em **português**. Exceção deliberada: os paths HTTP (`/api/health`, `/api/simulations`, `/api/simulations/compare`) ficam em inglês por serem contrato explícito da especificação original (`instrucoes.md`).

## Estrutura

```
backend/src/homepilot/core/      motor financeiro puro (dataclasses + Decimal, sem FastAPI/Pydantic)
backend/src/homepilot/esquemas/  Pydantic + conversão para o domínio
backend/src/homepilot/api/       endpoints FastAPI
frontend/src/                    Svelte + TS + Vite + Chart.js
```

O frontend nunca calcula nada financeiro — apenas envia dados e exibe o que o backend retorna.

Cada campo da tela tem um botão "?" (`componentes/Ajuda.svelte`) com sua explicação. Os textos moram num objeto `textos` no `<script>` do componente que tem os campos, não dentro do `Ajuda`. Ao mudar uma regra financeira, revisar esses textos — eles são a única explicação que o usuário final lê.

## Decisões financeiras chave

- Taxa de juros mensal = `taxa_nominal_anual / 12` (proporcionalidade simples), **não** a taxa efetiva informada no contrato. Confirmado numericamente para o cenário inicial: `(1+0,1002/12)^12-1 ≈ 10,49%`, batendo com a taxa efetiva do contrato.
- TR (e demais indexadores) convertida por juros compostos: `(1+taxa_anual)^(1/12)-1`.
- A prestação Price é **recalculada todo mês** com base no saldo corrigido e prazo restante vigentes, em vez de fixada uma única vez — isso resolve o ajuste da última parcela sem caso especial. O mesmo vale para a amortização do SAC (`saldo / prazo`).
- Aportes extraordinários da **mesma competência somam** (pontuais entre si, recorrentes entre si e uns com os outros). A regra antiga aplicava só o primeiro e descartava o resto — foi revogada porque um aporte recorrente mensal engoliria todo aporte pontual do contrato. Ver `docs/regras-financeiras.md` §4.0.
- Aportes recorrentes são uma **lista**, não um único registro: é o que permite mudar de patamar ao longo do contrato ("R$ 500/mês em 2026, R$ 1.500/mês em 2027") sem materializar centenas de eventos pontuais. Sobreposição entre recorrências é permitida e soma.
- Price e SAC diferem em apenas **dois pontos** do motor, ambos isolados em helpers de `core/simulador.py`: `_calcular_prestacao_e_amortizacao` (qual grandeza é calculada e qual é derivada) e `_calcular_prazo_apos_reducao` (qual grandeza é preservada na redução de prazo). Um terceiro sistema deve entrar por esses dois helpers, não espalhando `if` pelo laço mensal.
- Todo cálculo monetário usa `Decimal` com `ROUND_HALF_UP` a cada etapa — nunca `float`.

## Rodar e testar

```bash
cd backend && source .venv/bin/activate && pytest -q   # 80 testes
cd frontend && npm run build                            # build de produção
```

Ambiente desta máquina não tem `python3-venv` instalado (`python3 -m venv` falha com "ensurepip is not available"). Se o `.venv` precisar ser recriado, usar:

```bash
python3 -m venv --without-pip .venv
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python3 /tmp/get-pip.py -q
```

## Git

Confirmar com o usuário antes de criar commits — não commitar proativamente.
