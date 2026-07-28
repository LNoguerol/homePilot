# Roadmap

Status das etapas do HomePilot. Não é um cronograma com datas — apenas o que já existe, o que está desenhado e ainda não implementado, e o que é ideia futura sem desenho ainda.

## ✅ Feito

- Motor financeiro (Tabela Price, TR, amortização extraordinária por redução de prazo/prestação, alertas de limite) — `backend/src/homepilot/core/`.
- API FastAPI (`/api/simulations`, `/api/simulations/compare`, `/api/health`), com validação e tratamento de erros de negócio em HTTP 422.
- Frontend Svelte + TS + Vite + Chart.js: formulário de contrato, amortizações extras, resumo, três gráficos, tabela de cronograma, exportação CSV, comparação de cenários.
- Docker Compose para backend + frontend.
- 47 testes automatizados do backend (pytest) — 38 do motor financeiro + 9 de cadastro/login (rodam com SQLite local, sem exigir MariaDB).
- **Banco de dados (MariaDB)** — tabela `usuarios` (nome, e-mail, senha, telefone opcional, cidade, estado), conexão via SQLAlchemy, migration inicial via Alembic. Desenho em [`banco.md`](banco.md).
- **Autenticação** — cadastro (`POST /api/auth/cadastro`), login com JWT (`POST /api/auth/login`), rota protegida (`GET /api/auth/eu`), telas de login/cadastro no frontend com sessão via `localStorage`. Desenho em [`autenticacao.md`](autenticacao.md). As rotas de simulação continuam públicas (decisão registrada no documento).
- Documentação: `README.md`, [`arquitetura.md`](arquitetura.md), [`regras-financeiras.md`](regras-financeiras.md), [`padroes-desenvolvimento.md`](padroes-desenvolvimento.md).

## 🔜 Desenhado, ainda não implementado

Nada no momento — banco e autenticação, que estavam aqui, foram implementados (ver "✅ Feito").

## 💡 Ideias futuras (sem desenho ainda)

Levantadas a partir das limitações já documentadas em `README.md` §5 e do fato de que o cadastro de usuário abre espaço para funcionalidades que dependem de identidade:

- Salvar simulações por usuário (histórico de cenários simulados), reaproveitando a tabela `usuarios` já planejada.
- Série histórica real de TR mês a mês (Banco Central), em vez de cenário anual constante — a estrutura do motor já foi projetada pensando nisso (ver `regras-financeiras.md` §1.2).
- Recuperação de senha por e-mail.
- Suporte a outros sistemas de amortização além da Tabela Price (ex.: SAC), e outros indexadores além da TR.
- Deploy em nuvem (explicitamente fora de escopo na especificação original da v1).

## Como este documento deve ser mantido

Atualizar a seção "✅ Feito" conforme itens de "🔜 Desenhado" forem implementados, e mover ideias de "💡 Ideias futuras" para "🔜 Desenhado" quando alguém escrever o desenho correspondente (um novo arquivo em `docs/`, como foi feito para banco e autenticação).
