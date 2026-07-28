# Autenticação

> **Status:** implementado como desenhado — complementar a [`banco.md`](banco.md), que descreve a tabela `usuarios`. Este documento detalha o fluxo de autenticação em si (cadastro, login, proteção de rotas). As rotas de simulação (`/api/simulations`) permaneceram públicas, conforme a decisão registrada abaixo.

## Objetivo

Permitir que uma pessoa crie uma conta (nome, e-mail, senha, telefone opcional, cidade, estado) e faça login para acessar a aplicação. Nesta primeira etapa de autenticação, **toda conta autenticada tem o mesmo nível de acesso** — não há papéis/perfis (admin vs. usuário comum é explicitamente fora de escopo, ver `banco.md`).

## Endpoints

Adicionados a `backend/src/homepilot/api/` (novo módulo `auth.py`), prefixo `/api/auth`:

| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| `POST` | `/api/auth/cadastro` | nome, email, senha, telefone?, cidade, estado | usuário criado (sem senha/hash) |
| `POST` | `/api/auth/login` | email, senha | `{ "token": "...", "expira_em": "..." }` |
| `GET` | `/api/auth/eu` | — (requer token) | dados do usuário autenticado |

Nomes de rota mantidos em português (diferente de `/api/simulations`), pois autenticação é uma adição nova do projeto, não parte do contrato original da especificação em inglês.

## Cadastro

1. Validar formato de e-mail e unicidade (`SELECT` por e-mail antes do `INSERT`; a constraint `UNIQUE` no banco é a garantia final contra condição de corrida).
2. Validar senha mínima: pelo menos 8 caracteres. Não exigir regras artificiais de composição (maiúscula+número+símbolo) — evidência de usabilidade mostra que tamanho mínimo é mais eficaz que complexidade forçada.
3. Gerar `senha_hash` com bcrypt (custo padrão da biblioteca, hoje 12) antes de persistir. A senha em texto puro nunca é logada nem armazenada.
4. E-mail duplicado → HTTP 409 com mensagem em português ("Já existe uma conta com este e-mail.").
5. Falhas de validação de campo → HTTP 422 (mesmo padrão já usado nas simulações, via `ErroSimulacaoInvalida` ou equivalente para autenticação, ex. `ErroCadastroInvalido`).

## Login

1. Buscar usuário por e-mail.
2. Se não existir, ou se `bcrypt.verify(senha, senha_hash)` falhar: HTTP 401 com mensagem genérica ("E-mail ou senha inválidos.") — **nunca** revelar se o e-mail existe ou não, para não facilitar enumeração de contas.
3. Se válido: emitir um **JWT** assinado (`HOMEPILOT_JWT_SECRET`, algoritmo `HS256`), contendo `sub` (id do usuário) e `exp` (expiração — sugestão: 24h). Não incluir senha/hash no payload do token.
4. Devolver o token; o frontend o guarda (ver seção Frontend) e passa a enviá-lo em `Authorization: Bearer <token>`.

## Proteção de rotas

Uma dependency do FastAPI (`Depends(usuario_atual)`) decodifica e valida o JWT do header `Authorization`, busca o usuário correspondente e o injeta no endpoint. Token ausente, expirado ou inválido → HTTP 401.

Decisão a confirmar quando a implementação começar: se as rotas de simulação (`/api/simulations`) passam a exigir login ou continuam públicas. Enquanto não decidido, presumir que **continuam públicas** — autenticação é aditiva, não deve quebrar o uso atual sem login.

## Frontend

- Novo componente `TelaLogin.svelte` / `TelaCadastro.svelte` em `frontend/src/lib/componentes/`.
- Token guardado em `localStorage` (chave `homepilot_token`) — aceitável para esta etapa; não há dados sensíveis além do próprio token, e a exposição a XSS é o mesmo risco de qualquer SPA sem HttpOnly cookie. Reavaliar para cookie `HttpOnly` se o projeto crescer em sensibilidade.
- `api.ts` passa a anexar o header `Authorization` em todas as chamadas quando houver token salvo.
- Ao receber 401 de qualquer chamada, o frontend limpa o token e redireciona para a tela de login.

## Fora de escopo por enquanto

- Recuperação de senha por e-mail.
- Confirmação de e-mail no cadastro.
- Login social (Google etc.).
- Perfis/papéis de usuário.
- Rate limiting de tentativas de login (considerar antes de ir para produção real).
