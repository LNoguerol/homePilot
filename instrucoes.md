Quero iniciar um projeto chamado HomePilot.

O HomePilot será uma aplicação web para simulação e planejamento de financiamentos imobiliários brasileiros. A primeira versão deve permitir simular um contrato pela Tabela Price, considerar correção pela TR, amortizações extraordinárias com FGTS e acompanhar limites de saldo devedor e prestação.

Quero que você construa uma aplicação web funcional desde o início, mas mantenha o escopo como um MVP bem organizado, testável e evolutivo.

# 1. Stack tecnológica

Utilize:

Backend:
- Python 3.11+
- FastAPI
- Pydantic
- pytest
- Decimal para os cálculos financeiros
- Uvicorn

Frontend:
- Svelte com TypeScript
- Vite
- CSS simples e responsivo
- Não use uma biblioteca visual pesada neste primeiro ciclo
- Use Chart.js apenas se for necessário para os gráficos

Estrutura:
- Monorepo com backend e frontend separados
- O motor financeiro deve ficar desacoplado da API
- O frontend nunca deve implementar fórmulas financeiras
- Todos os cálculos devem ser feitos no backend

Não implemente autenticação, banco de dados, pagamentos, inteligência artificial ou deploy em nuvem nesta primeira versão.

# 2. Objetivo do MVP

O usuário deve conseguir:

1. Informar os dados do financiamento.
2. Configurar a TR.
3. Cadastrar amortizações extraordinárias.
4. Executar uma simulação mensal.
5. Visualizar os principais indicadores.
6. Visualizar a evolução do saldo e da prestação.
7. Consultar a tabela mensal completa.
8. Comparar cenários de TR.
9. Identificar se o saldo ultrapassa R$ 350.000,00.
10. Identificar se a prestação total ultrapassa R$ 3.800,00.

# 3. Dados iniciais do financiamento

Preencha o formulário inicialmente com estes valores:

- Data-base da simulação: 17/07/2026
- Saldo devedor: R$ 332.786,77
- Sistema de amortização: Tabela Price
- Indexador: TR
- Taxa nominal: 10,02% ao ano
- Taxa efetiva informada: 10,49% ao ano
- Prazo original: 390 meses
- Prazo restante estimado: 376 meses
- Seguros e tarifas mensais: R$ 130,00
- Limite máximo do saldo devedor: R$ 350.000,00
- Limite máximo da prestação total: R$ 3.800,00

Todos esses campos devem ser editáveis.

# 4. Amortizações com FGTS

Cadastre inicialmente os seguintes eventos:

- Junho de 2027: R$ 40.000,00
- Junho de 2029: R$ 40.000,00
- Junho de 2031: R$ 40.000,00
- Junho de 2033: R$ 40.000,00
- Junho de 2035: R$ 40.000,00

As amortizações devem utilizar redução de prazo como padrão.

O usuário deve conseguir:

- adicionar uma amortização;
- editar data e valor;
- excluir uma amortização;
- escolher entre redução do prazo e redução da prestação.

Nesta primeira versão, trate as datas e o intervalo do FGTS apenas como parâmetros configuráveis. Não codifique regras legais do FGTS como verdades permanentes.

# 5. Cenários de TR

Disponibilize inicialmente:

- TR anual de 0%
- TR anual de 1,5%
- TR anual de 2,0%
- TR anual de 2,5%

O usuário também deve poder informar manualmente uma TR anual personalizada.

Converta a taxa anual para uma taxa mensal equivalente pela fórmula:

taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

Estruture o backend para futuramente aceitar uma série histórica mensal de TR, embora isso não precise estar disponível na interface inicial.

# 6. Convenção simplificada do cálculo mensal

Antes de implementar, documente claramente as premissas.

Para esta versão, adote esta sequência:

1. Obter o saldo inicial do mês.
2. Aplicar a correção monetária pela TR.
3. Calcular os juros do período.
4. Calcular a prestação financeira pela Tabela Price.
5. Calcular a amortização ordinária:
   amortização = prestação financeira - juros
6. Aplicar a amortização ordinária.
7. Aplicar eventual amortização extraordinária.
8. Recalcular o prazo ou a prestação, conforme a estratégia selecionada.
9. Acrescentar seguros e tarifas para encontrar a prestação total.
10. Registrar o saldo final.

Não afirme que essa sequência reproduz exatamente o Bradesco. Documente no README que a ordem operacional, os arredondamentos, a data de aniversário contratual, seguros e critérios internos do banco podem gerar diferenças.

# 7. Tabela Price

Utilize a fórmula:

PMT = PV × [i × (1 + i)^n] / [(1 + i)^n - 1]

Onde:

- PMT é a prestação financeira;
- PV é o saldo financiado;
- i é a taxa mensal;
- n é o prazo restante.

A taxa mensal dos juros deve ser obtida de forma consistente a partir da taxa nominal contratual.

Documente qual conversão foi adotada.

Não misture a TR com a taxa de juros contratual dentro de uma única taxa. Mostre os dois efeitos separadamente no cronograma.

# 8. Redução do prazo

Para amortizações com redução de prazo:

- mantenha a prestação financeira vigente;
- reduza imediatamente o saldo devedor;
- recalcule quantos meses seriam necessários para quitar o novo saldo com aquela prestação;
- utilize uma fórmula financeira ou busca numérica segura;
- trate corretamente casos próximos da quitação;
- nunca permita saldo negativo;
- no último mês, ajuste a prestação ao valor necessário para encerrar o saldo.

# 9. Redução da prestação

Para amortizações com redução da prestação:

- mantenha o prazo restante;
- reduza o saldo;
- recalcule a prestação financeira pela fórmula Price.

# 10. Dados mensais da simulação

O backend deve gerar, em cada competência:

- número do mês;
- data da competência;
- saldo inicial;
- correção pela TR;
- saldo corrigido;
- juros;
- prestação financeira;
- amortização ordinária;
- amortização extraordinária;
- seguros e tarifas;
- prestação total;
- saldo final;
- prazo restante;
- estratégia aplicada;
- alerta de saldo;
- alerta de prestação.

# 11. Resumo da simulação

Apresente no frontend:

- saldo inicial;
- maior saldo devedor;
- maior prestação total;
- data prevista de quitação;
- quantidade de meses até a quitação;
- quantidade de meses antecipados;
- total pago em juros;
- total pago em correção pela TR;
- total pago em seguros e tarifas;
- total amortizado com recursos extraordinários;
- soma de todas as prestações;
- status do limite de saldo;
- status do limite de prestação.

Use formatação monetária brasileira:

R$ 332.786,77

Use datas no formato brasileiro:

17/07/2026
Junho/2027

# 12. Interface da aplicação

Crie uma aplicação com uma interface limpa e profissional.

Estrutura sugerida:

## Cabeçalho

- Nome: HomePilot
- Subtítulo: Planejamento inteligente para financiamento imobiliário

## Área de configuração

Organize os campos em seções:

- Dados do contrato
- Taxas e TR
- Seguros e tarifas
- Limites financeiros
- Amortizações extraordinárias

## Botões

- Simular
- Restaurar valores iniciais
- Adicionar amortização
- Exportar CSV

## Painel de resultados

Exiba cards com:

- Saldo projetado máximo
- Prestação máxima
- Quitação estimada
- Juros totais
- Economia estimada
- Situação dos limites

## Gráficos

Inclua:

1. Evolução mensal do saldo devedor.
2. Evolução da prestação total.
3. Composição acumulada entre juros, amortização, TR e seguros.

Os gráficos devem ter títulos, unidades e tooltips.

## Tabela

Inclua uma tabela mensal com:

- data;
- saldo inicial;
- TR;
- juros;
- amortização;
- amortização extraordinária;
- prestação total;
- saldo final.

Permita ocultar e exibir a tabela para não deixar a tela inicial muito extensa.

# 13. Comparação de cenários

Crie uma área de comparação que execute simultaneamente os cenários:

- TR 0%
- TR 1,5%
- TR 2,0%
- TR 2,5%

Exiba uma tabela comparativa com:

- cenário;
- quitação estimada;
- maior saldo;
- maior prestação;
- juros totais;
- total da TR;
- limite de saldo respeitado;
- limite de prestação respeitado.

# 14. API

Crie pelo menos os seguintes endpoints:

GET /api/health

Resposta:
{
  "status": "ok"
}

POST /api/simulations

Recebe os dados do contrato, cenário de TR e amortizações.
Retorna o resumo e o cronograma mensal.

POST /api/simulations/compare

Recebe os dados-base e uma lista de cenários de TR.
Retorna a comparação entre os cenários.

Inclua validações com mensagens compreensíveis para:

- saldo inválido;
- prazo menor ou igual a zero;
- taxa negativa;
- amortização negativa;
- data de amortização anterior à data-base;
- prestação insuficiente para pagar os juros;
- valores fora de faixas razoáveis.

# 15. Estrutura desejada

Crie algo semelhante a:

homepilot/
├── README.md
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── homepilot/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   └── simulations.py
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── price.py
│   │       │   ├── rates.py
│   │       │   ├── simulator.py
│   │       │   └── summaries.py
│   │       └── schemas/
│   │           ├── __init__.py
│   │           └── simulation.py
│   └── tests/
│       ├── test_price.py
│       ├── test_rates.py
│       ├── test_simulator.py
│       ├── test_extra_payments.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.svelte
│   │   ├── app.css
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── currency.ts
│   │   │   ├── types.ts
│   │   │   └── components/
│   │   │       ├── ContractForm.svelte
│   │   │       ├── ExtraPayments.svelte
│   │   │       ├── SummaryCards.svelte
│   │   │       ├── BalanceChart.svelte
│   │   │       ├── PaymentChart.svelte
│   │   │       ├── ScenarioComparison.svelte
│   │   │       └── ScheduleTable.svelte
│   │   └── main.ts
│   └── tests/
└── outputs/

A estrutura pode ser ajustada se você justificar a decisão.

# 16. Testes obrigatórios

Crie testes para:

- cálculo da prestação Price;
- conversão de taxa anual para mensal;
- conversão da TR anual para mensal;
- saldo nunca negativo;
- amortização extraordinária;
- redução de prazo;
- redução de prestação;
- quitação antecipada;
- ajuste da última parcela;
- alerta ao ultrapassar R$ 350.000,00;
- alerta ao ultrapassar R$ 3.800,00;
- comparação de cenários;
- validações dos endpoints.

Inclua ao menos um teste com cálculo manual simples e verificável.

# 17. Cenário inicial que deve funcionar

Ao abrir a aplicação, carregue:

- saldo: R$ 332.786,77;
- data-base: 17/07/2026;
- prazo restante: 376 meses;
- taxa nominal: 10,02% ao ano;
- TR: 1,5% ao ano;
- seguros e tarifas: R$ 130,00;
- limite do saldo: R$ 350.000,00;
- limite da prestação: R$ 3.800,00;
- amortizações de R$ 40.000,00 em junho de 2027 e a cada 24 meses;
- estratégia: redução do prazo.

Ao clicar em Simular, a aplicação deve:

- enviar os dados para o backend;
- calcular o cronograma;
- mostrar o resumo;
- desenhar os gráficos;
- preencher a tabela;
- informar se os limites foram respeitados.

# 18. Exportação

Implemente a exportação do cronograma para CSV no frontend.

O CSV deve utilizar:

- separador ponto e vírgula;
- decimal com vírgula;
- codificação UTF-8 com BOM;
- nomes de colunas em português.

Não implemente Excel ainda.

# 19. Docker

Inclua um docker-compose.yml para executar backend e frontend localmente.

Também documente a execução sem Docker.

Comandos esperados:

Backend:
- instalação;
- execução;
- testes.

Frontend:
- instalação;
- execução;
- build;
- testes, caso sejam configurados.

# 20. README

O README deve explicar:

- objetivo do projeto;
- arquitetura;
- instalação;
- execução;
- fórmulas usadas;
- ordem mensal dos cálculos;
- limitações do modelo;
- diferenças possíveis em relação ao Bradesco;
- como cadastrar amortizações;
- como comparar cenários;
- como executar os testes.

Inclua um aviso claro:

“Este projeto é uma ferramenta educacional e de planejamento. Os resultados são estimativas e não substituem o demonstrativo oficial da instituição financeira, orientação jurídica, contábil ou financeira.”

# 21. Forma de trabalho

Antes de alterar ou criar arquivos:

1. Inspecione o diretório atual.
2. Verifique se já existe algum projeto.
3. Apresente um plano curto de implementação.
4. Liste as principais premissas financeiras.
5. Identifique pontos ambíguos.
6. Faça perguntas apenas se alguma ambiguidade impedir a implementação.

Depois:

1. Crie a estrutura do projeto.
2. Implemente primeiro o motor financeiro.
3. Crie e execute os testes do backend.
4. Implemente a API.
5. Implemente o frontend.
6. Integre frontend e backend.
7. Execute a aplicação.
8. Corrija erros encontrados.
9. Execute todos os testes.
10. Apresente um resumo final.

Não pare somente após criar arquivos vazios ou uma estrutura inicial.

Quero que você entregue uma primeira versão funcional, executável localmente e com o cenário inicial preenchido.

# 22. Critérios de conclusão

Considere o primeiro ciclo concluído somente quando:

- o backend iniciar sem erros;
- o frontend iniciar sem erros;
- a API responder;
- a simulação inicial funcionar;
- os gráficos forem exibidos;
- a tabela mensal for preenchida;
- o CSV puder ser exportado;
- os testes do backend passarem;
- o README possuir instruções reproduzíveis;
- as limitações financeiras estiverem documentadas.

Ao final, informe:

- arquivos criados;
- decisões de arquitetura;
- fórmulas adotadas;
- resultados dos testes;
- comandos para iniciar o projeto;
- limitações conhecidas;
- próximos passos recomendados.
