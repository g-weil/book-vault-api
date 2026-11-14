# PostgreSQL local com Docker

PostgreSQL local para a migração da biblioteca. A transferência dos registros foi
executada e validada; o SQLite original está preservado. O Compose deste arquivo
`compose.postgres.yaml` inicia somente o banco; `compose.yaml` inicia banco e aplicação.

## Execução integrada após a migração

Com Docker Desktop aberto e `.env.postgres` já configurado, execute na raiz:

```powershell
docker compose up -d --build --wait
docker compose ps
```

Acesse `http://127.0.0.1:8000/` e `http://127.0.0.1:8000/docs`.
Não precisa iniciar Uvicorn em outro terminal. Os arquivos da aplicação são
copiados para a imagem: depois de editar código, reconstrua com o comando acima.
Para apenas iniciar novamente a instalação existente, use `docker compose up -d --wait`.

O serviço `book-vault` usa a rede Compose para acessar `postgres:5432`, enquanto
o acesso do Windows ao banco continua em `127.0.0.1:5432`. `depends_on` com
`service_healthy` aguarda o PostgreSQL aceitar conexões antes de iniciar a API.

Os dois arquivos Compose mantêm o mesmo projeto e volume da migração:
`book-vault-postgres-local_postgres-data`. Para a rotina, use `compose.yaml`,
selecionado automaticamente por `docker compose`. O arquivo separado fica para
preparação/diagnóstico do banco; os arquivos não representam bancos independentes.

Use `docker compose stop` para parar e `docker compose up -d --wait` para voltar.
`docker compose down` remove os contêineres, preservando o volume. Não use `down -v`.
Não altere o nome do projeto para esta instalação.

## Preparação

Mantenha o Docker Desktop aberto. Na raiz do projeto, copie o modelo:

```powershell
Copy-Item .env.postgres.example .env.postgres
```

Faça essa cópia somente se `.env.postgres` ainda não existir. Nesse arquivo,
substitua a senha de exemplo por uma senha local. Nunca envie esse arquivo ao Git;
ele já é ignorado. Se o ambiente já foi preparado, preserve a senha existente.

## Iniciar e verificar

```powershell
docker compose -f compose.postgres.yaml up -d --wait
docker compose -f compose.postgres.yaml ps
docker compose -f compose.postgres.yaml exec -T postgres psql -U bookvault -d book_vault -c "SELECT current_database(), current_user;"
```

O serviço deve aparecer como `healthy` e a consulta deve retornar `book_vault`
e `bookvault`. A imagem é baixada no primeiro início.

## Configuração

- `postgres:18`: imagem do PostgreSQL, mantendo a versão principal explícita.
- `env_file`: lê nome do banco, usuário e senha de `.env.postgres`.
- `127.0.0.1:5432:5432`: disponibiliza o banco somente neste computador.
- `postgres-data:/var/lib/postgresql`: volume persistente, com o caminho da imagem 18.
- `healthcheck`: verifica se o PostgreSQL aceita conexões; não testa a API nem a migração.
- `name`: mantém separado o projeto Compose do banco e o Compose atual da aplicação.

O usuário `bookvault` é administrador do banco para o desenvolvimento local.
A configuração de produção deverá usar um usuário da aplicação com permissões limitadas.
A consulta com `psql` dentro do contêiner usa a conexão local; a autenticação TCP
com senha será verificada quando conectarmos a API.

Se a porta 5432 já estiver ocupada, não encerre outro banco: altere somente a porta
do computador para `127.0.0.1:5433:5432` e utilize 5433 na futura conexão da API.

## Parar e iniciar novamente

```powershell
docker compose -f compose.postgres.yaml stop
docker compose -f compose.postgres.yaml start
```

Também é possível remover os contêineres mantendo o volume:

```powershell
docker compose -f compose.postgres.yaml down
docker compose -f compose.postgres.yaml up -d --wait
```

Não acrescente `-v` ao `down`: isso remove o volume e seus dados. Um volume não
substitui backups. Não troque a versão principal da imagem apontando para os mesmos
dados sem planejar a atualização do PostgreSQL.

As variáveis `POSTGRES_*` inicializam um volume vazio. Editar a senha no arquivo
depois da primeira execução não altera a senha de um banco já criado.

## Próximas etapas

### Conexão e operações preparadas — etapas 1 e 2

`requirements.txt` inclui `psycopg[binary]`, o driver usado pelo SQLAlchemy para
comunicar com PostgreSQL. Instale as dependências atualizadas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`database.py` aceita `DATABASE_URL` com prioridade sobre `BOOK_VAULT_DB_PATH`.
Exemplo de formato, sem credencial real:

```text
postgresql+psycopg://USUARIO:SENHA_CODIFICADA@127.0.0.1:5432/book_vault
```

URLs `postgresql://` e `postgres://` também selecionam Psycopg 3. Caracteres
especiais da senha precisam de codificação em URL; ao construir em Python, prefira
`sqlalchemy.engine.URL.create`, que recebe a senha original sem concatená-la.
Não compartilhe a URL real nem a grave em arquivos versionados.

Sem `DATABASE_URL`, a aplicação continua utilizando o SQLite anterior. O arquivo
`.env.postgres` é lido pelo Compose, não automaticamente pelo processo Python.

O teste de conexão com `engine.connect()` e `SELECT 1` verifica conectividade e
autenticação; criar o engine sozinho não verifica isso.

A inicialização agora cria as tabelas tanto em SQLite quanto em PostgreSQL, sem
apagá-las. Também preserva a adaptação aditiva da coluna de capa em bancos antigos.
Esse preparo usa `create_all` e inspeção; ainda não há um sistema geral de migrações
versionadas. Mudanças futuras na estrutura precisam ser planejadas separadamente.

As escritas usam `transacao_escrita`: no SQLite, `BEGIN IMMEDIATE`; no PostgreSQL,
um `pg_advisory_xact_lock` comum às operações da aplicação, com isolamento
`READ COMMITTED`. O bloqueio é adquirido antes das consultas de validação e é
liberado ao confirmar ou desfazer a transação. Isso serializa as escritas, mantendo
a proteção de duplicidade simples para uma biblioteca pessoal. Consultas comuns
não adquirem esse bloqueio. Clientes que escrevam diretamente no banco precisam
seguir o mesmo protocolo; a comparação título + conjunto de autores continua
sendo uma regra da aplicação, não uma restrição única simples do banco.

Cadastro, edição e exclusão de autores e livros, alteração de status e carga do
catálogo usam esse controle. Se houver volume elevado de escritas no futuro,
reavaliar essa estratégia para permitir maior concorrência.

**Sem `DATABASE_URL`, o código ainda usa SQLite por compatibilidade.** Depois da
transferência, inicie a API com a URL PostgreSQL para continuar usando a biblioteca
migrada. Não volte a cadastrar dados no SQLite, pois os dois bancos não sincronizam.
A API agora inicia pelo Compose com `POSTGRES_HOST=postgres` e os campos
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` do arquivo local. Não depende
de variável temporária do terminal. `DATABASE_URL` explícita continua tendo
prioridade; sem URL e sem `POSTGRES_HOST`, o comando antigo do Uvicorn ainda abre
SQLite. Utilize o Compose integrado para trabalhar com a biblioteca migrada.

### Backup e transferência — etapa 3

`migracao.py` faz uma cópia única e exige um PostgreSQL vazio. Não apaga nem mescla
registros existentes no destino. Não execute a API no destino antes da cópia:
a carga automática de gêneros já o deixaria preenchido.

Procedimento para uma nova instalação, não para repetir no banco já migrado:

1. Interromper a API e outras gravações no SQLite; manter o PostgreSQL disponível.
2. Configurar `BOOK_VAULT_MIGRATION_DATABASE_URL` no processo da transferência,
   com a URL do destino e as credenciais locais, sem versioná-las.
3. Executar na raiz:

```powershell
.\.venv\Scripts\python.exe migracao.py --origem book_vault.db --backups backups
```

4. Conferir o relatório das cinco tabelas e o caminho do backup.
5. Iniciar a API com `DATABASE_URL` apontando para o destino conferido.

A ferramenta bloqueia escritas SQLite durante a operação, gera um backup pela API
`sqlite3.backup`, verifica integridade e chaves estrangeiras e lê somente esse
snapshot. Copia primeiro as tabelas principais e depois os vínculos, preservando
os IDs. Uma comparação integral de campos e associações ocorre antes do commit.
Os geradores de IDs são ajustados por `ALTER SEQUENCE ... RESTART`, dentro da mesma
transação. Erros desfazem a cópia no PostgreSQL, preservando o SQLite e o backup.

O backup recebe nome único com data UTC e fica em `backups/`, ignorado pelo Git.
Mantenha também uma cópia fora deste computador. O relatório local da transferência
real está em `backups/migracao_postgres.json` e contém apenas caminho e contagens.

Na transferência local foram conferidos: 6 livros, 5 autores, 18 gêneros, 6 vínculos
livro/autor e 9 vínculos livro/gênero. Esses números descrevem o momento da cópia,
não a quantidade futura da biblioteca.

### Testes PostgreSQL isolados

`tests/test_postgres.py` reutiliza os testes HTTP, menu e JavaScript, acrescentando
inicialização repetida, rollback e cadastros/edições simultâneos.

Para habilitá-los, forneça `BOOK_VAULT_TEST_DATABASE_URL` ao processo de testes,
com acesso ao PostgreSQL local e permissão para criar bancos. Use o formato de URL
descrito acima e cuide da codificação da senha. A suíte cria um banco com nome
`book_vault_test_` seguido de UUID, testa somente nele e o remove ao concluir.
O banco indicado pela URL não tem suas tabelas excluídas ou preenchidas pelos testes.
Não use credenciais de produção. Sem essa variável, os testes PostgreSQL são
explicitamente ignorados; os testes SQLite continuam executando.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O workflow `.github/workflows/testes.yml` agora fornece PostgreSQL 18 como serviço
temporário, com healthcheck, e define `BOOK_VAULT_TEST_DATABASE_URL` para esse
ambiente. Verifica uma conexão real antes de executar a suíte. Também instala
Node.js para os testes JavaScript. O banco local, o volume da biblioteca e as
credenciais da VPS não são utilizados. A suíte cria seu próprio banco temporário
nesse servidor, incluindo os testes de backup e transferência.

O workflow executa em push, pull request e acionamento manual. Sua configuração
local não confirma uma execução no GitHub: após commit e push, confira o resultado
na aba Actions e os detalhes das etapas em caso de falha.

1. Atualizar o README para a configuração definitiva; o guia da VPS já descreve os dois serviços.
2. Commitar, enviar e conferir a execução do workflow no GitHub.

Referência: [imagem oficial PostgreSQL](https://hub.docker.com/_/postgres).
