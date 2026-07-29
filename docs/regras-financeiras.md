# Regras financeiras

Este documento detalha, com precisão de implementação, as regras de cálculo do motor financeiro (`backend/src/homepilot/core/`). É o complemento técnico da seção 4 do `README.md` — aqui entram as constantes, validações e casos de borda exatamente como implementados.

## 1. Taxas

### 1.1 Taxa de juros mensal (`taxas.taxa_nominal_anual_para_mensal`)

```
taxa_mensal_juros = taxa_nominal_anual / 12
```

Proporcionalidade simples. A taxa **efetiva** informada no contrato (`taxa_efetiva_informada`) é apenas um campo de referência/conferência — não entra em nenhum cálculo do laço mensal. Para o cenário inicial (nominal 10,02% a.a.), `(1 + 0,1002/12)^12 - 1 ≈ 10,4932% a.a.`, batendo com os 10,49% informados no contrato.

### 1.2 Taxa de indexador mensal (`taxas.taxa_anual_para_mensal_equivalente`)

```
taxa_mensal = (1 + taxa_anual)^(1/12) - 1
```

Juros compostos, usando `Decimal.ln()`/potência fracionária nativa (precisão padrão de 28 dígitos). Usada para a TR e preparada para outros indexadores que sigam a mesma convenção. Se `taxa_anual == 0`, retorna `0` diretamente (evita o caminho de potenciação desnecessário).

Cenários padrão de TR (`taxas.CENARIOS_TR_PADRAO`): 0,0% / 1,5% / 2,0% / 2,5% a.a.

## 2. Tabela Price

### 2.1 Prestação (`tabela_price.calcular_prestacao`)

```
PMT = PV * [i * (1+i)^n] / [(1+i)^n - 1]
```

- Se `taxa_mensal == 0`: `PMT = PV / n` (divisão linear).
- Se `prazo_meses <= 0`: levanta `ValueError` puro (erro de argumento, não deveria vir da API já validada pelo Pydantic).

### 2.2 Prazo para quitar (`tabela_price.calcular_prazo_para_quitar`)

Usado apenas na estratégia de **redução de prazo** após uma amortização extraordinária. Isola `n` na fórmula da Tabela Price, de forma contínua (não arredondada):

```
n = -ln(1 - i * saldo / prestacao) / ln(1 + i)
```

- Se `saldo <= 0`: retorna `0`.
- Se `taxa_mensal == 0`: `n = saldo / prestacao` (linear).
- Se `razao = 1 - i*saldo/prestacao <= 0` (prestação insuficiente para pagar os juros do saldo): levanta `ErroSimulacaoInvalida` — este é um erro de **negócio**, mapeado para HTTP 422, não um bug.

O resultado contínuo é arredondado para cima (`ROUND_CEILING`) para um inteiro de meses no laço principal, com piso de 1 mês (`max(1, ...)`).

## 2-A. SAC — Sistema de Amortização Constante

Selecionável em `contrato.sistema_amortizacao` (`"price"` — padrão — ou `"sac"`). A diferença entre os dois sistemas está inteiramente concentrada em **duas** decisões: como a dupla (prestação, amortização) é calculada no mês, e qual grandeza é preservada na redução de prazo. Todo o resto do laço mensal (correção pela TR, juros, alertas, limites, resumo) é idêntico.

| | Price | SAC |
|---|---|---|
| Grandeza calculada | prestação | amortização |
| Grandeza derivada | amortização = prestação - juros | prestação = amortização + juros |
| Perfil da prestação | ~constante (cresce com a TR) | decrescente |
| Perfil da amortização | crescente | ~constante |
| Total de juros | maior | menor |
| Preservado na redução de prazo | prestação financeira | amortização mensal |

### 2-A.1 Amortização constante (`tabela_sac.calcular_amortizacao_constante`)

```
A = PV / n
```

Não depende da taxa de juros — no SAC os juros entram apenas na composição da prestação. Se `prazo_meses <= 0`: levanta `ValueError` puro (mesma convenção da Price).

Como esta fórmula é reaplicada a cada mês sobre o **saldo corrigido** e o prazo restante vigentes, a amortização é constante *entre eventos*: ela se reajusta quando a TR corrige o saldo (subindo levemente) ou quando uma amortização extraordinária altera saldo/prazo. Com TR = 0% a.a. ela é literalmente constante, a menos de um centavo de resíduo de divisão redistribuído mês a mês.

### 2-A.2 Prazo para quitar (`tabela_sac.calcular_prazo_para_quitar`)

```
n = PV / A
```

Sempre linear, pois a amortização não depende dos juros. Se `saldo <= 0`: retorna `0`. Se `amortizacao_constante <= 0`: levanta `ValueError`. Aqui **não existe** o erro de negócio "prestação insuficiente para pagar os juros" que a Price pode produzir (§5.4): no SAC a amortização é paga *além* dos juros, nunca descontada deles.

### 2-A.3 Piso de um centavo

Se o saldo for pequeno demais em relação ao prazo para render um centavo por mês (`A` arredondaria para `0,00`), a amortização é forçada ao piso de `0,01` — limitado ao próprio saldo corrigido. Sem isso, o saldo nunca decresceria e a simulação bateria na trava de segurança de meses (§5.5). Situação inalcançável com valores realistas; é uma garantia de terminação, não uma regra financeira.

## 3. Laço mensal de simulação (`simulador.simular`)

Ordem exata das operações em cada mês (implementa README §4.7):

1. `saldo_inicial` = saldo do mês anterior (ou saldo do contrato, no mês 1).
2. `correcao_tr = arredondar(saldo_inicial * taxa_mensal_tr)`.
3. `saldo_corrigido = saldo_inicial + correcao_tr`.
4. `juros = arredondar(saldo_corrigido * taxa_mensal_juros)`.
5. `prestacao_financeira` e `amortizacao_ordinaria` pelo sistema do contrato (`_calcular_prestacao_e_amortizacao`, ver §2 e §2-A) — recalculadas todo mês, nunca fixadas:
   - **Price**: `prestacao = arredondar(calcular_prestacao(saldo_corrigido, taxa_mensal_juros, prazo_restante))` e `amortizacao = prestacao - juros`.
   - **SAC**: `amortizacao = arredondar(calcular_amortizacao_constante(saldo_corrigido, prazo_restante))` e `prestacao = arredondar(amortizacao + juros)`.
6. `saldo_apos_ordinaria = saldo_corrigido - amortizacao_ordinaria`.
7. Se houver aportes na competência (pontuais e/ou recorrente): `amortizacao_extra = min(soma_dos_aportes, saldo_apos_ordinaria)` (nunca deixa o saldo negativo); aplica-se a estratégia (ver seção 4).
8. Caso contrário: `prazo_restante` decrementa em 1 (piso 0).
9. `prestacao_total = arredondar(prestacao_financeira + seguros_tarifas_mensais)`.
10. Registra a `ParcelaMensal` com os alertas (`alerta_saldo = saldo_final > limite_saldo`, `alerta_prestacao = prestacao_total > limite_prestacao`).
11. Repete enquanto `saldo > 0 and prazo_restante > 0`.

### Competência do mês

`_somar_meses(data_base, numero_mes)` soma meses de calendário à data-base preservando o dia, com clamp para o último dia do mês quando o mês de destino é mais curto (ex.: data-base dia 31 cai em fevereiro → vira o último dia de fevereiro). O casamento de uma amortização com o mês corrente usa `_mesma_competencia` (mesmo ano e mês, ignora o dia).

### Arredondamento

Todo valor monetário é arredondado a centavos (`ROUND_HALF_UP`) a cada etapa intermediária, nunca só no final — isso inclui `correcao_tr`, `saldo_corrigido`, `juros`, `prestacao_financeira`, `amortizacao_ordinaria`, `amortizacao_extraordinaria`, `seguros_tarifas`, `prestacao_total` e `saldo_final`.

## 4. Amortização extraordinária

Há duas formas de entrada, que convivem:

- **Aportes pontuais** — lista de `AmortizacaoExtraordinaria` (data, valor, estratégia), um item por evento.
- **Aporte recorrente** — um único `AporteRecorrente` (valor, periodicidade em meses, mês inicial, mês final opcional, estratégia), expandido pelo motor mês a mês. Existe para expressar em cinco campos o que exigiria centenas de eventos pontuais ("R$ 500 a mais todo mês até quitar"). Nunca é materializado como lista.

### 4.0 Soma dos aportes da competência (`_aportes_da_competencia`)

**Todos os aportes de um mesmo mês somam**: pontuais entre si e com o recorrente.

> Regra anterior, revogada: o motor aplicava apenas o primeiro aporte da competência e descartava os demais. Isso era tolerável quando só existiam eventos pontuais, mas com um aporte recorrente mensal passaria a descartar silenciosamente **todo** aporte pontual do contrato — um aporte de FGTS de R$ 40.000 desapareceria sem aviso. O teste `test_aporte_pontual_e_recorrente_no_mesmo_mes_somam` trava o comportamento novo.

A **estratégia** vigente no mês é a do primeiro aporte pontual (por ser ato mais deliberado que uma recorrência configurada uma única vez); a estratégia do recorrente só vale nos meses sem nenhum aporte pontual. Quando dois pontuais da mesma competência têm estratégias diferentes, vale a do primeiro na lista ordenada por data.

O valor somado é sempre limitado ao saldo disponível (`min(total, saldo_apos_ordinaria)`), então nenhum aporte deixa o saldo negativo.

### 4.0.1 Incidência da recorrência (`_recorrencia_incide_em`)

Um aporte recorrente incide na competência quando, sendo `d` a distância em meses entre a competência e `mes_inicial`:

```
d >= 0   e   d % periodicidade_meses == 0   e   (mes_final é None ou competência <= mes_final)
```

Comparações em granularidade de **ano/mês** — o dia de `mes_inicial`/`mes_final` é irrelevante, como já ocorria no casamento dos aportes pontuais. Como a fase é ancorada em `mes_inicial`, uma recorrência anual iniciada em 07/2026 cai nos julhos seguintes mesmo que 07/2026 não chegue a ser simulado.

Validações (`validar_aporte_recorrente`): `valor > 0`, `1 <= periodicidade_meses <= 600`, `mes_inicial` não anterior à competência da data-base, e `mes_final >= mes_inicial` quando informado.

### 4.1 Redução de prazo

Preserva a grandeza característica do sistema e resolve o prazo a partir dela (`_calcular_prazo_apos_reducao`), arredondando para cima com piso de 1 mês:

- **Price**: mantém a `prestacao_financeira` já calculada naquele mês → `tabela_price.calcular_prazo_para_quitar(saldo_apos_extra, taxa_mensal_juros, prestacao_financeira)`.
- **SAC**: mantém a `amortizacao_ordinaria` daquele mês → `tabela_sac.calcular_prazo_para_quitar(saldo_apos_extra, amortizacao_ordinaria)`.

Em ambos os casos o efeito visível é o mesmo: a parcela segue no mesmo patamar e a quitação é antecipada.

### 4.2 Redução de prestação

- Mantém o `prazo_restante` (decrementado em 1 neste mês, como o caso sem evento).
- A prestação do(s) mês(es) seguinte(s) cai naturalmente, pois é recalculada pelo sistema do contrato com o novo saldo (menor) e o mesmo prazo restante — na Price via novo PMT, no SAC via nova amortização (`saldo / prazo`), que arrasta a prestação para baixo junto com os juros do saldo menor.

### 4.3 Quitação por amortização

Se `saldo_apos_extra <= 0` após o evento: `prazo_restante` é forçado para `1`, e no fechamento do mês `saldo_final` é zerado e `prazo_restante` vai a `0` — a simulação termina neste mês, qualquer que fosse a estratégia escolhida no evento.

## 5. Validações de negócio (`ErroSimulacaoInvalida` → HTTP 422)

### 5.1 Contrato (`validar_contrato`)

| Condição | Mensagem |
|---|---|
| `saldo_devedor <= 0` | saldo devedor inválido, deve ser > 0 |
| `saldo_devedor > 100.000.000` (`LIMITE_SALDO_RAZOAVEL`) | fora de faixa razoável |
| `prazo_original <= 0` | prazo original deve ser > 0 |
| `prazo_restante <= 0` | prazo restante deve ser > 0 |
| `prazo_restante > 600` (`LIMITE_PRAZO_RAZOAVEL`) | fora de faixa razoável |
| `taxa_nominal_anual < 0` | taxa nominal não pode ser negativa |
| `taxa_efetiva_informada < 0` | taxa efetiva não pode ser negativa |
| `taxa_nominal_anual > 1` (100% a.a., `LIMITE_TAXA_ANUAL_RAZOAVEL`) | fora de faixa razoável |
| `seguros_tarifas_mensais < 0` | não pode ser negativo |
| `limite_saldo <= 0` ou `limite_prestacao <= 0` | limites devem ser > 0 |

### 5.2 Amortizações (`validar_amortizacoes`)

- `valor <= 0` → inválido.
- `data < data_base do contrato` → inválido (não pode haver aporte antes do início da simulação).

### 5.3 TR (`validar_taxa_tr`)

- `taxa_anual < 0` → inválido.
- `taxa_anual > 1` (100% a.a.) → fora de faixa razoável.

### 5.4 Prestação insuficiente para pagar os juros

**Exclusiva da Price**, onde a amortização é o resíduo da prestação. No SAC a amortização é somada aos juros, então a prestação é suficiente por construção e nenhuma das duas checagens abaixo se aplica.

Checada duas vezes:
- **No mês 0** (antes do laço), com a prestação inicial: se `prestacao_inicial <= saldo * taxa_mensal_juros`, aborta antes de simular qualquer mês.
- **Dentro de `tabela_price.calcular_prazo_para_quitar`**, ao recalcular o prazo após uma redução de prazo, se a prestação mantida não bastar para cobrir os juros do novo saldo.

Na prática, para qualquer `n` finito e `i > 0`, o PMT da Tabela Price é sempre estritamente maior que o juro puro — este erro só é alcançável através de `calcular_prazo_para_quitar` chamado com uma combinação artificial de saldo/prestação/taxa, não através do laço normal de `simular()`.

### 5.5 Trava de segurança de meses

`LIMITE_MESES_SEGURANCA = 720` (60 anos). Se a simulação ultrapassar esse número de meses sem quitar o saldo, levanta `ErroSimulacaoInvalida` — proteção contra loop efetivamente infinito por parâmetros inconsistentes.

## 6. Resumo agregado (`resumos.montar_resumo`)

Calculado a partir do cronograma já pronto (`list[ParcelaMensal]`), sem reprocessar nenhuma fórmula financeira:

- `maior_saldo_devedor` = `max(saldo_final)` de todas as parcelas.
- `maior_prestacao_total` = `max(prestacao_total)`.
- `total_juros`, `total_correcao_tr`, `total_seguros_tarifas`, `total_amortizado_extraordinario`, `soma_prestacoes` = somas simples das colunas correspondentes.
- `meses_ate_quitacao` = número da última parcela.
- `meses_antecipados = max(0, prazo_restante_do_contrato - meses_ate_quitacao)`.
- `status_limite_saldo` / `status_limite_prestacao` = `"Ultrapassado"` se **qualquer** parcela tiver `alerta_saldo`/`alerta_prestacao` verdadeiro, senão `"Dentro do limite"`.

## 7. O que este motor deliberadamente não faz

Ver README §5 para a lista completa de limitações frente a um extrato bancário real (ordem operacional do banco, TR mensal real do BC em vez de cenário anual constante, política real de seguros/tarifas, regras legais de FGTS). Aqui, adicionalmente: o motor não soma TR e juros em uma única taxa composta (ficam sempre em colunas separadas), e admite um único aporte recorrente por simulação (aportes com periodicidades diferentes exigem cadastrar os pontuais).
