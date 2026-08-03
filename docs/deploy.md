# Deploy em produção (custo zero via Oracle Cloud Free Tier)

> **Status:** guia de infraestrutura, não faz parte do código da aplicação. Descreve como colocar o HomePilot no ar usando a camada "Always Free" da Oracle Cloud (VM ARM sempre gratuita), sem domínio próprio — acesso via IP público.

## 1. Visão geral

A aplicação roda inteira em **uma única VM**, via `docker-compose.prod.yml` (raiz do repositório):

```
[usuário] --80--> [container frontend: Nginx serve o build estático + proxy /api] --> [container backend: uvicorn] --> [container banco: MariaDB]
```

Diferenças em relação ao `docker-compose.yml` de desenvolvimento:

- `frontend` deixa de ser o servidor de dev do Vite e passa a servir o build de produção (`npm run build`) via Nginx, que também faz proxy de `/api` para o backend — um único ponto de entrada na porta 80, sem CORS entre origens diferentes.
- `backend` roda sem `--reload` e com `--workers 2`.
- `banco` não expõe porta ao host (só a rede interna do compose acessa) e usa senha vinda do `.env`, não a senha de desenvolvimento fixa no `docker-compose.yml`.
- Segredos (`HOMEPILOT_DB_SENHA`, `HOMEPILOT_JWT_SECRET`) vêm de um arquivo `.env` que **não é commitado** (ver `.env.example`).

## 2. Criar a VM Always Free na Oracle Cloud

1. Criar conta em [cloud.oracle.com](https://cloud.oracle.com) (pede cartão de crédito para verificação, mas a camada Always Free não cobra).
2. No console web (não é terminal): clicar no menu ☰ no canto superior esquerdo → **Compute → Instances → Create Instance**.
3. Na seção "Image and shape", clicar em **Edit** e escolher a imagem **Canonical Ubuntu 22.04** com o shape **VM.Standard.A1.Flex (aba "Ampere")** — é o shape elegível ao Always Free (até 4 OCPUs / 24 GB, gratuito para sempre). **Imagem e shape precisam ser da mesma arquitetura** (ARM/aarch64 para A1.Flex): se o console reclamar de shape incompatível com a imagem, reabra a seleção de imagem com a opção "mostrar apenas imagens compatíveis com o shape" marcada. Se aparecer erro de `Out of host capacity`, é falta de capacidade ARM da Oracle na região naquele momento — tentar de novo mais tarde ou trocar de região, não é erro de configuração.
4. Em "Add SSH keys", colar uma chave pública já existente ou deixar o console gerar um par novo para download (arquivo `.key` privado + `.key.pub` público).
5. Na seção **"Networking"**, na parte **"Public IPv4 address assignment"**, marcar **"Automatically assign public IPv4 address"**. Esse campo é fácil de passar batido e, se ficar desmarcado, a instância sobe sem IP público (campo aparece como `-` na listagem depois). Reaproveitar a VCN/sub-rede pública já existente se você já tiver criado uma instância antes.
6. Criar a instância e anotar o **IP público**.
7. Se mesmo assim o IP público ficar `-`: a causa mais comum é a sub-rede não estar conectada à internet ainda. Na página da VCN tem um atalho **"Quick actions" → "Connect public subnet to internet"**, que configura automaticamente Internet Gateway, Route Table e um Network Security Group (`ig-quick-action-NSG`). Isso resolve o roteamento, mas **não** atribui o IP público em si — se ainda faltar, ir na VNIC da instância → aba "IPv4 Addresses" → **⋮ → Edit** no IP privado → escolher **"Ephemeral Public IP"**.
8. Abrir a porta 80 para a internet (duas camadas, as duas são necessárias):
   - **Security List / Network Security Group** da VCN (inclui o `ig-quick-action-NSG` se foi criado no passo 7): adicionar regra de entrada permitindo TCP porta 80 de `0.0.0.0/0` (e porta 22 para SSH, se ainda não estiver lá).
   - **Firewall interno do Ubuntu** (`iptables`/`netfilter`, já rodando por padrão nas imagens Oracle): rodar na VM:
     ```bash
     sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
     sudo netfilter-persistent save   # ou: sudo apt install iptables-persistent
     ```

**Testando a conectividade:** `ping <IP_PUBLICO>` não é um bom teste — a Oracle não libera ICMP echo por padrão nas regras criadas automaticamente, então ping sem resposta não indica problema. O teste real é SSH.

**Problema comum de SSH — `sign_and_send_pubkey: signing failed ... agent refused operation`:** é um bug conhecido do agente de chaves do Ubuntu (gnome-keyring) com certas chaves. Se aparecer isso ao conectar, corrigir permissão do arquivo da chave privada e desligar o agente só para esse comando:

```bash
chmod 600 /caminho/da/chave-privada.key   # nunca use o arquivo .pub aqui, é a pública
SSH_AUTH_SOCK= ssh -i /caminho/da/chave-privada.key ubuntu@<IP_PUBLICO>
```

## 3. Instalar Docker na VM

Já conectado via SSH:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
newgrp docker
```

## 4. Subir a aplicação

```bash
git clone <url-do-seu-repositorio> homePilot
cd homePilot
cp .env.example .env
nano .env   # preencher HOMEPILOT_DB_SENHA, HOMEPILOT_DB_SENHA_ROOT, HOMEPILOT_JWT_SECRET com valores fortes e únicos

docker compose -f docker-compose.prod.yml up -d --build
```

O backend roda `alembic upgrade head` automaticamente antes de subir o uvicorn (ver `backend/Dockerfile`), então a tabela `usuarios` já existe na primeira subida.

Verificar:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://localhost/api/health   # {"status":"ok"}
```

Acessar `http://<IP_PUBLICO>` no navegador.

## 5. Atualizando após mudanças no código

```bash
cd homePilot
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## 6. Limitações desta configuração (sem domínio)

- Acesso é via HTTP puro no IP (`http://<IP_PUBLICO>`), sem HTTPS — navegadores mostram "não seguro" e a senha de login trafega sem criptografia. Aceitável para teste/uso pessoal, **não recomendado** se outras pessoas forem se cadastrar com senhas reais.
- Quando quiser resolver isso sem gastar com domínio: um subdomínio gratuito (ex. DuckDNS, ou um domínio `.xyz`/`.tech` de baixo custo) apontando para o IP, mais [Caddy](https://caddyserver.com/) como reverse proxy no lugar do Nginx, dá HTTPS automático via Let's Encrypt sem configuração manual de certificados. Avisar se quiser que eu prepare esse passo depois.
- Backup do MariaDB: o volume `banco_dados` persiste no disco da VM, mas não há backup automático fora dela. Para algo além de teste, considerar `mysqldump` periódico para outro lugar (ex. Oracle Object Storage, dentro do free tier de 10 GB).
