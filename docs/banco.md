# Banco de dados

> **Status:** implementado (tabela `usuarios`, conexão SQLAlchemy, migration Alembic). A especificação original (`instrucoes.md`, linha 32) dizia explicitamente para não incluir banco de dados nem autenticação na primeira versão do HomePilot — esta foi uma expansão de escopo posterior, decidida diretamente com a usuária, não uma reinterpretação da especificação original.

## Motivação

Introduzir cadastro de usuário (nome, e-mail, senha, telefone opcional, cidade, estado) e login na página, como base para autenticação. Por enquanto isso não altera o motor de simulação (`core/`), que continua stateless — o banco serve apenas para autenticação/identidade de usuário.

## Tecnologia

**MariaDB**. Acesso a partir do backend FastAPI via SQLAlchemy (ORM) + Alembic (migrations), mantendo o mesmo padrão de camadas já usado no projeto: modelos de banco ficam isolados em uma camada própria, sem vazar para `core/` (o motor financeiro continua sem depender de banco).

```
backend/src/homepilot/
├── core/          motor financeiro puro (inalterado, sem banco)
├── esquemas/       Pydantic (API)
├── api/            endpoints FastAPI
├── bd/             NOVO: conexão, modelos ORM, migrations
│   ├── conexao.py    engine SQLAlchemy + sessão
│   ├── modelos.py     modelos ORM (tabela usuarios)
│   └── migracoes/     Alembic
└── auth/           NOVO: hash de senha, login, emissão/validação de token
```

## Tabela `usuarios`

| Coluna | Tipo | Regras |
|---|---|---|
| `id` | `BIGINT UNSIGNED AUTO_INCREMENT` | chave primária |
| `nome` | `VARCHAR(150)` | obrigatório |
| `email` | `VARCHAR(255)` | obrigatório, único (índice `UNIQUE`) |
| `senha_hash` | `VARCHAR(255)` | obrigatório — **nunca** armazenar senha em texto puro |
| `telefone` | `VARCHAR(20)` | opcional (`NULL`) |
| `cidade` | `VARCHAR(100)` | obrigatório |
| `estado` | `CHAR(2)` | obrigatório — sigla UF |
| `criado_em` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` |
| `atualizado_em` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` |

```sql
CREATE TABLE usuarios (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NULL,
    cidade VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

`utf8mb4` é necessário para nomes de cidade/pessoa com acentuação e eventuais emojis, sem os problemas do `utf8` antigo do MySQL/MariaDB.

## Senha e login

- Hash da senha com **bcrypt** (via `passlib` ou `bcrypt` diretamente) — nunca `md5`/`sha1`/texto puro.
- Login: endpoint recebe e-mail + senha, verifica o hash, e devolve um **JWT** (via `python-jose` ou `pyjwt`) com expiração curta, usado depois como `Authorization: Bearer <token>` nas rotas protegidas.
- Cadastro: endpoint valida e-mail único (erro 422/409 em caso de duplicata) e força de senha mínima antes de gerar o hash.
- Nenhuma senha, hash incluído, deve aparecer em logs.

## Configuração e ambiente

Credenciais via variáveis de ambiente (nunca hardcoded):

```
HOMEPILOT_DB_HOST=localhost
HOMEPILOT_DB_PORT=3306
HOMEPILOT_DB_NOME=homepilot
HOMEPILOT_DB_USUARIO=homepilot
HOMEPILOT_DB_SENHA=<segredo>
HOMEPILOT_JWT_SECRET=<segredo>
```

`HOMEPILOT_DB_PORT=3306` é o padrão para um MariaDB nativo na máquina. Ao usar o serviço `banco` do Docker Compose (ver abaixo), a porta exposta no host é **3307** — para evitar conflito com uma instalação local de MariaDB já usando 3306 — então `HOMEPILOT_DB_PORT` deve ser `3307` quando o backend roda fora do Docker mas aponta para esse container.

## Docker Compose

Novo serviço a adicionar ao `docker-compose.yml` existente:

```yaml
  banco:
    image: mariadb:11
    environment:
      MARIADB_DATABASE: homepilot
      MARIADB_USER: homepilot
      MARIADB_PASSWORD: homepilot
      MARIADB_ROOT_PASSWORD: root
    ports:
      - "3307:3306"
    volumes:
      - banco_dados:/var/lib/mysql

volumes:
  banco_dados:
```

O serviço `backend` passa a depender de `banco` (`depends_on`) e recebe as variáveis `HOMEPILOT_DB_*` apontando para `banco` em vez de `localhost` — internamente na rede do Docker isso continua na porta 3306 (o remapeamento para 3307 só afeta quem acessa a partir do host).

## Migrations

Alembic gerencia a evolução do schema (criação da tabela `usuarios` como primeira migration, e futuras alterações) em vez de scripts SQL soltos ou `create_all()` direto — importante já que o schema deve evoluir (ex.: tabela de simulações salvas, se vier a ser pedida).

## Fora de escopo por enquanto

- Recuperação de senha por e-mail (esqueci minha senha).
- Perfis/papéis de usuário (admin vs. usuário comum).
- Persistência de simulações/contratos no banco — o motor de simulação continua stateless; isso seria uma extensão futura separada desta.
