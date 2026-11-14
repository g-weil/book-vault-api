# Executar o Book Vault na VPS com Docker

O Compose executa dois serviços: `book-vault` (FastAPI e frontend) e `postgres`
(PostgreSQL 18). A aplicação usa usuário sem root e Uvicorn sem reload. O banco
armazena seus arquivos em volume persistente montado em `/var/lib/postgresql`.

## Preparar

Instale Docker Engine e Docker Compose pela [documentação oficial](https://docs.docker.com/engine/install/).
Clone a versão do projeto com `Dockerfile`, `compose.yaml`, `compose.postgres.yaml`
e `frontend/`. As mudanças locais precisam estar commitadas e enviadas ao GitHub.
Não copie `.venv`, bancos ou credenciais dentro da imagem.

Em instalação nova, copie `.env.postgres.example` para `.env.postgres` e escolha
credenciais exclusivas da VPS. Não sobrescreva um arquivo de configuração existente.
O modelo usa um administrador PostgreSQL para desenvolvimento; para produção,
planeje um usuário da aplicação com permissões limitadas.

O Compose lê o arquivo local para os dois serviços. A aplicação recebe
`POSTGRES_HOST=postgres` e `POSTGRES_PORT=5432`, construindo a URL com a senha
original, inclusive caracteres especiais. Não coloque uma `DATABASE_URL` local
nesse arquivo, pois ela teria prioridade sobre esses campos.

## Iniciar e verificar

```bash
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
docker compose logs --tail=100 book-vault
```

`config --quiet` valida sem imprimir as credenciais. A API aguarda o banco ficar
healthy antes de iniciar. O healthcheck da aplicação consulta `/generos`.
O estado unhealthy sozinho não reinicia o serviço; a política de reinício atua
quando o processo encerra.

Em instalação nova, o volume começa vazio e a aplicação cria tabelas e gêneros.
Os livros locais não são enviados automaticamente. Na máquina onde a migração já
ocorreu, o Compose reutiliza o volume com os livros existentes.

O projeto chama-se `book-vault-postgres-local` para preservar o volume da migração:
`book-vault-postgres-local_postgres-data`. Não troque o nome nem use outro `-p`
numa instalação existente sem planejar a mudança; isso pode criar outro volume e
aparentar perda de dados. Esse nome interno não define o domínio público.
Instalações antigas com SQLite precisam de transferência separada: esta atualização
não apaga nem importa automaticamente seus volumes anteriores.

## Acessar

A aplicação publica `127.0.0.1:8000`; o banco publica `127.0.0.1:5432` apenas no host.
Os contêineres comunicam-se internamente por `postgres:5432`.

Na própria VPS, confira:

```bash
curl -f http://127.0.0.1:8000/generos
```

Para acesso privado, no seu computador:

```powershell
ssh -L 8080:127.0.0.1:8000 usuario@IP_DA_VPS
```

Com o túnel aberto, use `http://127.0.0.1:8080/` e `http://127.0.0.1:8080/docs`.
Frontend e API usam a mesma origem; não é necessário outro servidor web ou CORS.
Para domínio público, configure proxy com HTTPS e controle de acesso. A aplicação
não possui autenticação; quem alcançar seus endpoints poderá alterar a biblioteca.
Um proxy no host acessa `127.0.0.1:8000`; se estiver na mesma rede Compose, acessa
`book-vault:8000`.

Se a porta da aplicação estiver ocupada, no Linux é possível iniciar com
`PORT=8001 docker compose up -d --build --wait` e ajustar túnel/proxy para 8001.
Não exponha a porta do banco na internet.

## Atualizar e parar

Após obter alterações no código:

```bash
docker compose up -d --build --wait
```

Para apenas voltar a executar uma instalação existente:

```bash
docker compose up -d --wait
```

O Compose utiliza os arquivos copiados na imagem; mudanças no código exigem build.
Não é necessário iniciar Uvicorn no terminal. O menu local continua usando a API.
`docker compose stop` para os serviços. `docker compose down` remove os contêineres
mas mantém o volume. **Não use `docker compose down -v`**, pois remove os dados.

## Backup do PostgreSQL

Use `pg_dump` para obter um backup lógico consistente. O exemplo grava um arquivo
no contêiner e depois copia para o host:

```bash
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/book-vault.dump'
docker compose cp postgres:/tmp/book-vault.dump ./book-vault-backup.dump
```

Use nomes diferentes para preservar backups anteriores. Guarde cópias fora da VPS
e teste a restauração em banco separado. Não versione `.dump`, `.db` ou credenciais.
O volume não substitui backups. Não restaure sobre dados existentes sem planejar e
aprovar essa operação.

O Docker precisa iniciar após reiniciar o computador/servidor. A política
`unless-stopped` permite retomar contêineres que estavam executando, mas não liga
Docker Desktop nem contêineres que foram parados manualmente.
