# Bot de Cagada Remunerada para Discord

Projeto completo, didático e funcional de um bot para Discord com Python, `discord.py`, Docker e MariaDB.

Ele foi pensado para dois objetivos ao mesmo tempo:

- funcionar de verdade em produção simples
- ser fácil de estudar lendo o código

## O que o projeto faz

O bot registra pausas remuneradas em tom humorístico, separando tudo por servidor Discord.

Com ele você consegue:

- iniciar uma cagada remunerada
- finalizar a cagada aberta
- gerar relatório individual
- gerar relatório geral do servidor
- calcular tempo médio
- gerar ranking do servidor

Os comandos foram implementados como slash commands:

- `/cagada iniciar`
- `/cagada finalizar`
- `/cagada relatorio`
- `/cagada media`
- `/cagada ranking`

## Estrutura do projeto

```text
.
├── app
│   ├── cogs
│   │   ├── __init__.py
│   │   └── cagada.py
│   ├── repositories
│   │   ├── __init__.py
│   │   └── poop_break_repository.py
│   ├── services
│   │   ├── __init__.py
│   │   └── poop_break_service.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── time_utils.py
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── logging_config.py
│   └── main.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── schema.sql
├── scripts
│   └── setup_env.py
└── README.md
```

## Visão rápida da arquitetura

### `app/main.py`

Ponto de entrada do projeto.

Responsável por:

- carregar `.env`
- configurar logs
- conectar no banco
- garantir que a tabela existe
- carregar os comandos do bot
- sincronizar os slash commands

### `app/config.py`

Lê e valida as variáveis de ambiente.

### `app/db.py`

Cria e gerencia o pool de conexões com MariaDB.

### `app/repositories/poop_break_repository.py`

Faz o acesso direto ao banco com SQL.

### `app/services/poop_break_service.py`

Contém a regra de negócio:

- impedir duas cagadas abertas
- finalizar sessão
- calcular duração
- montar relatórios
- montar ranking combinado

### `app/cogs/cagada.py`

Expõe os slash commands do Discord.

### `schema.sql`

Mostra claramente a estrutura da tabela principal.

## Como o bot conversa com o Discord

De forma simples:

1. você cria o bot no Discord Developer Portal
2. o Discord gera um token secreto para ele
3. o programa Python usa esse token para autenticar
4. o bot fica conectado ao Discord
5. quando alguém usa um slash command, o Discord envia o evento para o bot
6. o bot processa o comando, consulta o banco e responde no servidor

Ou seja: o Discord não acessa seu banco diretamente.  
Quem faz isso é o seu código Python.

## Como o bot sabe em qual servidor o comando foi executado

Cada interação enviada pelo Discord carrega o `guild_id`, que é o ID único do servidor.

Esse ID é salvo no banco junto com o registro.  
Assim o bot consegue:

- separar dados de servidores diferentes
- gerar ranking por servidor
- evitar misturar relatórios

## Por que usamos `guild_id` no banco

Porque o mesmo bot pode estar em vários servidores ao mesmo tempo.

Sem `guild_id`, o ranking de um servidor poderia puxar dados de outro, o que seria errado.

## Por que não usar `root` no banco

Porque `root` tem permissões demais.

Boa prática:

- criar um banco específico
- criar um usuário específico para o bot
- dar apenas as permissões necessárias

Exemplo:

```sql
CREATE DATABASE discord_paid_breaks CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'discord_bot'@'%' IDENTIFIED BY 'uma_senha_bem_forte';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON discord_paid_breaks.* TO 'discord_bot'@'%';
FLUSH PRIVILEGES;
```

## Banco de dados

Tabela principal: `poop_break_sessions`

Campos:

- `id`
- `guild_id`
- `user_id`
- `user_name`
- `started_at`
- `finished_at`
- `duration_seconds`
- `status`
- `created_at`
- `updated_at`

O projeto executa o `schema.sql` no startup com `CREATE TABLE IF NOT EXISTS`, então a tabela é criada automaticamente se ainda não existir.

## Variáveis de ambiente

Se você quiser preencher o `.env` de forma guiada, rode o assistente CLI:

### Linux

```bash
python scripts/setup_env.py
```

### Windows PowerShell

```powershell
python .\scripts\setup_env.py
```

Ele pergunta item por item, mostra um resumo, grava o `.env` e pode subir o ambiente com `docker compose up -d --build` logo em seguida.

Copie o arquivo de exemplo:

### Linux

```bash
cp .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Exemplo de `.env`

```env
DISCORD_BOT_TOKEN=cole_o_token_real_aqui
DISCORD_SYNC_GUILD_ID=123456789012345678

DB_HOST=mariadb
DB_PORT=3306
DB_NAME=discord_paid_breaks
DB_USER=discord_bot
DB_PASSWORD=sua_senha_forte

TZ=America/Sao_Paulo
LOG_LEVEL=INFO
DB_POOL_MIN_SIZE=1
DB_POOL_MAX_SIZE=10
DB_DOCKER_NETWORK=mariadb-net
```

### O que cada variável significa

- `DISCORD_BOT_TOKEN`: token secreto do bot
- `DISCORD_SYNC_GUILD_ID`: opcional, mas muito útil para testes rápidos de slash commands
- `DB_HOST`: host do MariaDB
- `DB_PORT`: porta do MariaDB
- `DB_NAME`: nome do banco
- `DB_USER`: usuário do banco
- `DB_PASSWORD`: senha do banco
- `TZ`: fuso horário usado nas exibições e filtros
- `LOG_LEVEL`: nível de log
- `DB_POOL_MIN_SIZE` e `DB_POOL_MAX_SIZE`: tamanho do pool de conexões
- `DB_DOCKER_NETWORK`: rede Docker externa onde está o MariaDB central

## Mentoria de deploy: quais dados você precisa trazer para preencher o `.env`

Antes de subir o ambiente, você precisa juntar estas informações:

- `DISCORD_BOT_TOKEN`: vem do Discord Developer Portal
- `DISCORD_SYNC_GUILD_ID`: ID do seu servidor de teste no Discord
- `DB_HOST`: nome do MariaDB dentro da rede Docker
- `DB_PORT`: normalmente `3306`
- `DB_NAME`: nome do banco do bot
- `DB_USER`: usuário dedicado do bot
- `DB_PASSWORD`: senha desse usuário
- `DB_DOCKER_NETWORK`: no seu caso, normalmente `mariadb-net`

Na prática, para o primeiro teste, o mínimo que você precisa descobrir agora é:

- token do bot
- client id da aplicação
- guild id do servidor de teste
- host/nome do serviço do MariaDB na rede `mariadb-net`
- usuário, senha e nome do banco

## Como criar o bot no Discord Developer Portal

### 1. Abra o portal

[Discord Developer Portal](https://discord.com/developers/applications)

### 2. Crie uma aplicação

- clique em `New Application`
- dê um nome para sua aplicação

Sugestão:

- `Cagada Remunerada Bot`

### 3. Crie o bot

Dentro da aplicação:

- entre na aba `Bot`
- clique em `Add Bot`

### 4. Copie o token

Na área do bot, gere/copiei o token e coloque no `.env`:

```env
DISCORD_BOT_TOKEN=seu_token_aqui
```

Guarde esse valor com cuidado.  
Quem tiver esse token controla o bot.

### 5. Pegue o Client ID

Anote o `Application ID` ou `Client ID`.  
Você vai usar esse valor para convidar o bot ao servidor.

### 6. Pegue o Guild ID do seu servidor de teste

No Discord, faça isso:

1. vá em `Configurações do Usuário`
2. entre em `Avançado`
3. ative `Modo Desenvolvedor`
4. volte para a lista de servidores
5. clique com o botão direito no servidor de teste
6. clique em `Copiar ID`

Esse valor entra em:

```env
DISCORD_SYNC_GUILD_ID=123456789012345678
```

Isso é muito útil porque acelera a aparição dos slash commands durante os testes.

## Como convidar o bot para o servidor

Monte a URL abaixo e troque `SEU_CLIENT_ID`:

```text
https://discord.com/oauth2/authorize?client_id=SEU_CLIENT_ID&scope=bot%20applications.commands&permissions=0
```

### O que essa URL faz

- `bot`: adiciona o bot no servidor
- `applications.commands`: habilita slash commands
- `permissions=0`: esse projeto não precisa de permissões administrativas para o caso atual

Abra a URL no navegador, escolha o servidor e conclua a autorização.

## Onde pegar cada informação no Discord, de forma objetiva

### `DISCORD_BOT_TOKEN`

No Developer Portal:

1. abra sua aplicação
2. entre em `Bot`
3. use `Reset Token` ou `Copy`
4. cole no `.env`

### `Client ID`

No Developer Portal:

1. abra sua aplicação
2. vá em `General Information`
3. copie `Application ID`

### `DISCORD_SYNC_GUILD_ID`

No app do Discord:

1. ative `Modo Desenvolvedor`
2. clique com o botão direito no servidor
3. escolha `Copiar ID`

## Sequência prática para subir o ambiente de teste

### Passo 1. Rodar o assistente de `.env`

```bash
python scripts/setup_env.py
```

No final, o próprio assistente pode:

- salvar o `.env`
- executar `docker compose up -d --build`
- abrir `docker compose logs -f remuneration-bot`

### Passo 2. Buscar os dados do Discord

Preencha no assistente:

- token do bot
- guild id do servidor de teste

Se ainda não tiver o token e o client id, siga a seção do Developer Portal acima e depois volte ao assistente.

### Passo 3. Preencher os dados do MariaDB

Para seu ambiente atual, provavelmente ficará algo perto disso:

```env
DB_HOST=mariadb
DB_PORT=3306
DB_NAME=discord_paid_breaks
DB_USER=discord_bot
DB_PASSWORD=sua_senha
DB_DOCKER_NETWORK=mariadb-net
```

Se o serviço do banco na rede Docker tiver outro nome, ajuste o `DB_HOST`.

### Passo 4. Convidar o bot para o servidor

Monte a URL de convite usando o `Client ID`, abra no navegador e adicione no servidor de teste.

### Passo 5. Subir o bot

```bash
docker compose up -d --build
```

### Passo 6. Confirmar pelos logs

```bash
docker compose logs -f remuneration-bot
```

Você quer ver mensagens como:

- conexão com o banco feita
- schema verificado
- slash commands sincronizados
- bot conectado no Discord

### Passo 7. Testar no servidor

No Discord:

- `/cagada iniciar`
- `/cagada finalizar`
- `/cagada relatorio`

## Comandos disponíveis

### `/cagada iniciar`

Cria um registro com:

- `guild_id`
- `user_id`
- `user_name`
- horário de início
- status `aberta`

Regras:

- não permite duas cagadas abertas para o mesmo usuário no mesmo servidor

### `/cagada finalizar`

Fecha a cagada aberta do usuário no servidor atual.

Grava:

- horário de fim
- duração em segundos
- status `concluida`

### `/cagada relatorio`

Pode gerar:

- relatório pessoal
- relatório geral do servidor

Parâmetros:

- `periodo`: `mes_atual`, `7d`, `30d`
- `visao`: `pessoal` ou `servidor`
- `usuario`: opcional no modo pessoal

Exemplos:

- `/cagada relatorio`
- `/cagada relatorio periodo:7d`
- `/cagada relatorio visao:servidor`
- `/cagada relatorio usuario:@Fulano`

### `/cagada media`

Compara a média do usuário com a média geral do servidor.

Exemplos:

- `/cagada media`
- `/cagada media periodo:30d`

### `/cagada ranking`

Mostra:

- top por quantidade
- top por tempo total
- ranking combinado

Exemplos:

- `/cagada ranking`
- `/cagada ranking periodo:7d`

## Filtros de período

Hoje o projeto suporta:

- `mes_atual`
- `7d`
- `30d`

O padrão é `mes_atual`.

Se quiser criar outros filtros depois, o melhor ponto para começar é:

- `app/utils/time_utils.py`

## Rodando localmente sem Docker

Opcional, mas útil para estudo.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.main
```

## Rodando com Docker

### 1. Preencha o `.env`

Configure:

- token do Discord
- host do MariaDB
- usuário e senha
- nome do banco

### 2. Entenda a rede externa do banco

O `docker-compose.yml` já está pronto para conectar o bot numa rede Docker externa:

```yaml
networks:
  mariadb_external:
    external: true
    name: ${DB_DOCKER_NETWORK:-mariadb-net}
```

No seu cenário, isso conversa bem com o MariaDB central que você já mantém em outra stack.

Se a rede realmente se chama `mariadb-net`, basta deixar:

```env
DB_DOCKER_NETWORK=mariadb-net
```

### 3. Configure o host do banco

Se o serviço do MariaDB na outra stack atende pelo nome `mariadb`, então:

```env
DB_HOST=mariadb
```

Se o nome na rede for outro, ajuste esse valor.

### 4. Suba o projeto

```bash
docker compose up -d --build
```

### 5. Veja os logs

```bash
docker compose logs -f remuneration-bot
```

### 6. Reinicie

```bash
docker compose restart
```

### 7. Atualize depois de mudar o código

```bash
docker compose down
docker compose up -d --build
```

## Exemplo de deploy em `/srv/src`

```bash
cd /srv/src
git clone <url-do-repo> remuneration-discord-bot
cd remuneration-discord-bot
cp .env.example .env
nano .env
docker compose up -d --build
```

## Como testar os comandos

### Teste 1. Ver se os slash commands apareceram

Se você configurou `DISCORD_SYNC_GUILD_ID`, os comandos costumam aparecer rápido no servidor informado.

Sem isso, comandos globais podem demorar mais para propagar.

### Teste 2. Abrir uma sessão

```text
/cagada iniciar
```

Esperado:

- o bot responde confirmando
- o banco recebe um registro com status `aberta`

### Teste 3. Tentar abrir outra sem fechar a primeira

```text
/cagada iniciar
```

Esperado:

- o bot bloqueia
- avisa que já existe uma cagada aberta

### Teste 4. Finalizar a sessão

```text
/cagada finalizar
```

Esperado:

- `finished_at` preenchido
- `duration_seconds` calculado
- status `concluida`

### Teste 5. Ver relatório pessoal

```text
/cagada relatorio
```

### Teste 6. Ver relatório do servidor

```text
/cagada relatorio visao:servidor
```

### Teste 7. Ver ranking

```text
/cagada ranking
```

## Problemas comuns e soluções

### Os comandos slash não aparecem

Verifique:

- se o bot foi convidado com `applications.commands`
- se `DISCORD_SYNC_GUILD_ID` foi configurado para seu servidor de testes
- se o bot reiniciou depois da sincronização

### O bot não conecta no banco

Verifique:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- se o bot entrou na rede `mariadb-net`

### O horário está errado

Ajuste:

```env
TZ=America/Sao_Paulo
```

Depois reinicie o container.

### O bot sobe, mas o comando falha

Veja os logs:

```bash
docker compose logs -f remuneration-bot
```

## Decisões de arquitetura

### Por que `discord.py`

Porque é a opção mais conhecida, madura e simples para esse tipo de bot.

### Por que slash commands

Porque são o padrão moderno do Discord.

Eles ajudam em:

- descoberta de comandos
- validação de parâmetros
- melhor experiência para o usuário

### Por que separar `repository`, `service` e `cog`

Para deixar o projeto fácil de manter e fácil de aprender:

- `repository`: conversa com o banco
- `service`: aplica a regra de negócio
- `cog`: conversa com o Discord

## Próximas melhorias possíveis

- adicionar testes automatizados
- criar comando para cancelar sessão aberta
- exportar relatórios em CSV
- adicionar permissões para relatórios administrativos
- criar dashboard web

## Resumo

Com este projeto você já tem:

- bot real com slash commands
- MariaDB externo suportado
- Docker e Docker Compose prontos
- relatórios por período
- ranking por servidor
- código separado por responsabilidade
- documentação pensada para aprendizado

Se quiser, o próximo passo ideal é eu te guiar arquivo por arquivo, explicando a arquitetura e o fluxo completo do `/cagada iniciar` até a gravação no MariaDB.
