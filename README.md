# Book Vault API

Biblioteca pessoal para organizar livros, autores, gêneros e o andamento das leituras. Projeto de estudo e portfólio com API REST, interface web e menu de terminal.

## Funcionalidades e tecnologias

- Cadastro, consulta, edição e exclusão de livros e autores.
- Biblioteca em cards, capas opcionais e formulários em modais.
- Busca por título e autor, combinada com filtro de status.
- Vários autores e gêneros por livro, com catálogo fixo de 18 gêneros.
- Cinco status: **Quero ler**, **Lendo**, **Lido**, **Relendo** e **Abandonado**.
- Validação de dados, prevenção de duplicidades e persistência em PostgreSQL.
- Migração de SQLite para PostgreSQL com backup, preservação de IDs e conferência dos registros.
- Dois contêineres integrados pelo Docker Compose: aplicação e banco de dados.
- Testes de API, frontend, terminal, concorrência e transferência de dados, com workflow no GitHub Actions.

| Camada | Tecnologias |
| --- | --- |
| API | Python, FastAPI e Uvicorn |
| Modelagem e validação | SQLAlchemy e Pydantic |
| Banco principal | PostgreSQL 18, com driver Psycopg 3 |
| Compatibilidade e migração | SQLite |
| Interface web | HTML, CSS e JavaScript puro |
| Testes | unittest, HTTP e JavaScript com Node.js |
| Implantação | Docker e Docker Compose |

## Executar com Docker — recomendado

Instale Docker com Docker Compose. No Windows, abra o Docker Desktop e aguarde o mecanismo iniciar. Python, PostgreSQL e as dependências da aplicação são instalados nas imagens; não é necessário instalá-los diretamente no computador para usar a interface web. Node.js também não é necessário para executar a aplicação.

```bash
git clone https://github.com/g-weil/book-vault-api.git
cd book-vault-api
```

Na primeira instalação, crie o arquivo local de configuração. No PowerShell:

```powershell
Copy-Item .env.postgres.example .env.postgres
```

No Linux ou macOS:

```bash
cp .env.postgres.example .env.postgres
```

**Faça a cópia somente se `.env.postgres` ainda não existir.** Abra o arquivo e substitua a senha de exemplo por uma senha local. Não sobrescreva as credenciais de uma instalação existente nem envie esse arquivo ao Git. Alterar a senha no arquivo não altera automaticamente a senha de um banco já inicializado.

Na raiz do projeto, valide a configuração e inicie os serviços:

```bash
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
```

O comando baixa as imagens necessárias, constrói a aplicação e inicia os dois serviços em segundo plano. Ambos devem aparecer como `healthy`. Não é necessário executar Uvicorn em outro terminal.

| Acesso | Endereço |
| --- | --- |
| Interface web | http://127.0.0.1:8000/ |
| Swagger | http://127.0.0.1:8000/docs |
| OpenAPI | http://127.0.0.1:8000/openapi.json |

A aplicação serve a API e os arquivos estáticos do frontend no mesmo contêiner. O PostgreSQL fica em outro contêiner, com volume persistente. A API aguarda o banco estar pronto e cria as tabelas e o catálogo de gêneros, sem apagar registros existentes. Uma instalação nova começa sem livros; a biblioteca do desenvolvedor não é incluída na imagem.

Se aparecer `ERR_CONNECTION_REFUSED`, confira se o Docker está executando e consulte `docker compose ps` e `docker compose logs --tail=100 book-vault`. Atualizar a página não inicia o servidor.

### Iniciar novamente, atualizar e parar

```bash
# Iniciar uma instalação já construída
docker compose up -d --wait

# Reconstruir após alterar o código ou as dependências
docker compose up -d --build --wait

# Parar os serviços sem remover os contêineres
docker compose stop
```

O código é copiado para a imagem; mudanças locais exigem reconstrução. `docker compose down` remove os contêineres e preserva o volume. **Não use `docker compose down -v` se quiser manter os dados.** Um volume persistente não substitui backups.

## Como usar a interface web

### Cadastrar livro

1. Abra o formulário de cadastro na biblioteca.
2. Informe o título. A capitalização digitada é preservada e os espaços são normalizados.
3. Informe os autores, separados por ponto e vírgula. Se deixar em branco, será utilizado **Autor desconhecido**.
4. Escolha pelo menos um gênero do catálogo.
5. Selecione um dos cinco status. O campo é obrigatório, sem valor padrão.
6. Opcionalmente, informe uma URL HTTP/HTTPS de imagem para a capa e confirme.

O banco guarda somente o endereço da capa. O navegador carrega a imagem desse endereço; se estiver vazio ou a imagem falhar, aparece uma capa padrão.

Um livro é duplicado quando possui o mesmo título normalizado e o mesmo conjunto de autores, independentemente da ordem dos nomes. Títulos iguais com conjuntos de autores diferentes são permitidos.

Ao tentar cadastrar um livro existente:

- Se o status também for igual, a interface informa que o livro já está cadastrado e já possui esse status.
- Se o status for diferente, oferece a alteração mediante confirmação. Somente o status é alterado; os demais dados do livro existente são preservados.

### Consultar a biblioteca

Os cards mostram título, autores, gêneros, capa e status atual.

- **Título:** digite parte do nome e selecione uma sugestão para localizar um livro específico. As sugestões distinguem os livros pelos autores e ID.
- **Autor:** digite parte do nome, selecione um autor encontrado e consulte seus livros.
- **Status:** selecione o estado de leitura desejado.

Os filtros podem ser combinados e limpos separadamente. As buscas são atualizadas enquanto você digita; Enter antecipa a pesquisa. Use a atualização da biblioteca para buscar novamente os dados após alterações feitas pelo Swagger ou terminal.

Título e autor são pesquisados pela API. O filtro de status é aplicado pelo JavaScript sobre os livros recebidos. As comparações normalizam espaços e usam `casefold()`, sem remover acentos.

Uma biblioteca vazia apresenta **Sua biblioteca está vazia**. Consultas sem resultados são bem-sucedidas e retornam HTTP 200.

### Editar livro, capa e status

| Ação no card | Comportamento |
| --- | --- |
| Editar livro | Altera título, autores, gêneros e capa; envia apenas os campos modificados. |
| Atualizar status | Permite escolher um dos cinco status e confirmar. |
| Editar capa | Altera ou remove o endereço da imagem. |

Mantenha os valores preenchidos para preservar o que não deseja alterar. Uma lista de autores ou gêneros enviada substitui a lista anterior inteira: para manter dois autores, ambos devem continuar na lista.

Deixar autores em branco na edição preserva os atuais; não os substitui por Autor desconhecido. Pelo menos um gênero continua obrigatório. Apagar a URL remove a capa personalizada. Cancelar não grava alterações.

A edição não permite criar uma combinação de título e autores já pertencente a outro livro. Alterar autores em um livro muda seus vínculos; para renomear um autor em todos os livros, use a área **Autores**.

### Excluir livro

Use a ação de exclusão no card, confira o livro apresentado e confirme. A exclusão é definitiva e remove o livro e seus vínculos, preservando os cadastros dos autores e gêneros.

A API responde com HTTP **204**, sem corpo de resposta. A interface remove o card após o sucesso.

### Gerenciar autores

Selecione **Autores** na barra lateral para listar nomes e IDs, inclusive autores sem livros.

- **Consultar:** pesquise por parte do nome ou liste todos.
- **Cadastrar:** informe um nome não vazio. Um nome normalizado já existente é rejeitado.
- **Editar:** altere o nome mantendo o mesmo ID. A mudança aparece em todos os livros vinculados.
- **Excluir:** confira o autor e confirme. Só é permitido quando não possui livros vinculados; caso contrário, a API retorna HTTP 409.

## Menu de terminal

Com a aplicação executando pelo Compose, utilize Python 3.12 no computador para iniciar o menu. Na primeira utilização, prepare o ambiente virtual e as dependências.

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe menu.py
```

Linux ou macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python menu.py
```

O menu consome a API em `http://127.0.0.1:8000` por padrão e utiliza o mesmo banco da interface web. Oferece cadastro e consulta de livros, busca por autor, alteração de status, gerenciamento de autores, edição e exclusão de livros.

Separe autores por ponto e vírgula e IDs dos gêneros por vírgula. As opções de gêneros e status são exibidas antes da escolha. Na edição, entradas em branco preservam os dados atuais. Use `0` nas opções indicadas para voltar ou sair. Busca por título e gestão de capas estão disponíveis na web e na API, sem formulário específico no menu.

## Endpoints da API

| Método | Rota | Operação | Sucesso |
| --- | --- | --- | --- |
| GET | `/livros` | Consultar e filtrar livros | 200 |
| POST | `/livros` | Cadastrar livro | 201 |
| PATCH | `/livros/{livro_id}` | Editar dados do livro | 200 |
| PATCH | `/livros/{livro_id}/status` | Alterar status | 200 |
| DELETE | `/livros/{livro_id}` | Excluir livro | 204 |
| GET | `/autores` | Listar ou buscar autores | 200 |
| POST | `/autores` | Cadastrar autor | 201 |
| PATCH | `/autores/{autor_id}` | Editar autor | 200 |
| DELETE | `/autores/{autor_id}` | Excluir autor sem livros | 204 |
| GET | `/generos` | Consultar catálogo fixo | 200 |

No Swagger, abra a operação, clique em **Try it out**, preencha os parâmetros e use **Execute** para conferir o código e o corpo da resposta.

### Consultas

```text
GET /livros
GET /livros?titulo=hobbit
GET /livros?autor_id=1
GET /livros?autor_nome=tolkien
GET /livros?titulo=hobbit&autor_id=1
GET /autores?nome=tolkien
GET /generos
```

Use IDs obtidos no seu banco. O título pode ser combinado com um filtro de autor. Enviar `autor_id` e `autor_nome` juntos retorna 422. Não há parâmetro de status em `GET /livros`; esse filtro é aplicado na interface web.

### Cadastro e edição

Para cadastrar com `POST /livros`, consulte antes `GET /generos` e substitua o ID do exemplo por um existente:

```json
{
  "titulo": "O Hobbit",
  "autores": ["J. R. R. Tolkien"],
  "genero_ids": [1],
  "status": "Quero ler",
  "capa_url": null
}
```

A resposta contém `mensagem`, `livro` e `autores_reutilizados`. Autores existentes são reutilizados; os demais são criados na mesma transação. Omitir `autores` ou enviar uma lista vazia utiliza Autor desconhecido.

Em `PATCH /livros/{livro_id}`, envie somente os campos desejados:

```json
{
  "titulo": "O Hobbit: Uma Jornada Inesperada",
  "capa_url": null
}
```

Campos omitidos são preservados. `capa_url: null` remove a capa; os demais campos editáveis não aceitam `null`. Para autores e gêneros, envie a lista completa desejada em `autores` ou `genero_ids`.

Para alterar o status, use `PATCH /livros/{livro_id}/status`:

```json
{
  "status": "Lendo"
}
```

Para cadastrar ou editar um autor, use respectivamente `POST /autores` ou `PATCH /autores/{autor_id}`:

```json
{
  "nome": "J. R. R. Tolkien"
}
```

### Respostas e validações

| Código | Significado |
| --- | --- |
| 200 | Consulta ou alteração bem-sucedida, inclusive consulta vazia. |
| 201 | Cadastro realizado. |
| 204 | Exclusão realizada, sem JSON na resposta. |
| 404 | Registro solicitado para edição ou exclusão não encontrado. |
| 409 | Duplicidade ou exclusão de autor com livros vinculados. |
| 422 | Dados inválidos, campos obrigatórios ausentes ou filtros incompatíveis. |

Status diferentes das cinco opções são rejeitados com orientação sobre os valores permitidos. IDs devem ser positivos; títulos vazios e gêneros inexistentes não são aceitos.

## Modelagem e regras

O PostgreSQL é o banco da execução pelo Compose. A biblioteca local foi transferida do SQLite com IDs e vínculos preservados e comparação integral antes e depois do commit. O SQLite original foi mantido como cópia anterior, sem sincronização automática com PostgreSQL. Consulte o [guia de PostgreSQL local](docs/POSTGRES_LOCAL.md).

- `livros`: título, título normalizado, status e URL opcional da capa.
- `autores`: nome e nome normalizado, com unicidade do nome normalizado.
- `generos`: catálogo fixo, sem cadastro livre pelo usuário.
- `livros_autores` e `livros_generos`: relações muitos-para-muitos, sem repetição do mesmo par de IDs.
- A identidade do livro considera título normalizado e conjunto de autores; status, capa e gêneros não definem duplicidade.
- Escritas são transacionais: alterações relacionadas são confirmadas juntas ou desfeitas em caso de erro.
- No PostgreSQL, as operações de escrita da aplicação usam um bloqueio transacional compartilhado antes das validações, impedindo duplicidades em requisições simultâneas. No SQLite, a compatibilidade utiliza `BEGIN IMMEDIATE`. Escritas SQL externas precisam respeitar o mesmo protocolo; a identidade por título e conjunto de autores é uma regra da aplicação.

As decisões detalhadas estão em [REQUISITOS.md](REQUISITOS.md). A inicialização também trata a adição da coluna de capa em bancos da versão anterior. `create_all` e essa alteração aditiva não substituem um sistema geral de migrações versionadas.

### Transferir uma biblioteca SQLite existente

`migracao.py` gera um backup consistente, verifica integridade e vínculos, copia as cinco tabelas em ordem de dependência e compara os registros integralmente antes de confirmar. Preserva IDs e ajusta as sequências dos próximos cadastros. Falhas desfazem a cópia no PostgreSQL e preservam o backup.

**O destino precisa estar vazio.** A ferramenta recusa sobrescrever ou mesclar dados. A API deve ficar parada durante a transferência; iniciá-la antes em um destino novo já cria o catálogo e deixa esse banco preenchido.

Para uma biblioteca que ainda não foi migrada, configure `BOOK_VAULT_MIGRATION_DATABASE_URL` no processo com a URL PostgreSQL do destino e execute pelo ambiente Python local:

```powershell
.\.venv\Scripts\python.exe migracao.py --origem book_vault.db --backups backups
```

Não repita esse comando no banco já migrado. Os backups ficam fora do Git e da imagem. Preserve cópias também fora do computador; depois da troca, use somente PostgreSQL para novos cadastros. Veja o [procedimento detalhado](docs/POSTGRES_LOCAL.md).

## Testes

### Execução automática no GitHub

O workflow [Testes automatizados](.github/workflows/testes.yml) executa a suíte a cada `push` e `pull request`. Também pode ser iniciado manualmente pela aba **Actions**, em **Run workflow**, quando o arquivo estiver na branch padrão.

O workflow prepara Linux, Python 3.12, Node.js 24 e um serviço PostgreSQL 18 temporário. Aguarda o healthcheck do banco, verifica uma conexão real e executa os testes SQLite, PostgreSQL, menu, frontend e transferência. As credenciais são exclusivas desse ambiente descartável; o workflow não acessa a biblioteca pessoal, a VPS nem faz implantação.

Após enviar as alterações, abra a aba **Actions** ou os checks da pull request. Em caso de falha, consulte as etapas de conexão e **Executar testes SQLite, PostgreSQL, menu e frontend**. Para impedir merges com testes falhando, configure uma regra de proteção da branch exigindo o check **API, menu e frontend**. A execução local não confirma o resultado no GitHub; o workflow atualizado precisa ser enviado e conferido remotamente.

### Execução local

Prepare o ambiente Python e instale `requirements.txt` conforme os comandos da seção do menu. Execute na raiz:

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Linux ou macOS:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

Para habilitar também PostgreSQL, forneça `BOOK_VAULT_TEST_DATABASE_URL` ao processo de testes, apontando para um servidor de desenvolvimento acessível, com permissão para criar um banco descartável. Exemplo de formato, sem credenciais reais:

```text
postgresql+psycopg://USUARIO:SENHA_CODIFICADA@127.0.0.1:5432/BANCO
```

O arquivo `.env.postgres` é lido pelo Compose, não automaticamente pelo Python executado no computador. Configure a variável separadamente e não exponha a URL real no Git ou em mensagens. Caracteres especiais na senha exigem codificação quando inseridos em uma URL textual.

Os testes PostgreSQL criam um banco `book_vault_test_` com sufixo aleatório, executam somente nele e o removem ao concluir; não removem tabelas do banco indicado pela URL. Sem a variável, esses testes são explicitamente ignorados. Os testes SQLite usam memória ou arquivos temporários.

A suíte completa executada localmente passou nos **40 testes**, sem testes ignorados, com PostgreSQL e Node.js disponíveis. Cobre CRUD, filtros, validações, vínculos, concorrência, rollback, inicialização repetida, preservação dos dados e IDs na transferência e rejeição de destino preenchido. Os dados pessoais não são utilizados como massa de testes.

Se Node.js estiver disponível, a suíte também verifica interações do JavaScript com um DOM simplificado e requisições reais à API temporária. Isso não substitui testes visuais e de interação em um navegador. Node.js não é necessário para executar a aplicação.

Para uma verificação manual, cadastre um livro de teste, localize-o pelos filtros, altere o status, edite os dados e exclua-o. Confira que o autor permanece cadastrado e só pode ser excluído quando não tiver outros livros vinculados.

## Docker e VPS

O Compose mantém dois serviços na mesma rede:

```text
Navegador ou menu
        |
        v
book-vault: API FastAPI + frontend
        |
        v
postgres: PostgreSQL 18
        |
        v
Volume persistente postgres-data
```

Na rede interna, a API usa `postgres:5432`. No computador, os acessos publicados são `127.0.0.1:8000` para a aplicação e `127.0.0.1:5432` para o banco. `localhost` dentro da API apontaria para o próprio contêiner, não para PostgreSQL.

Para conferir o estado e os logs:

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 book-vault
docker compose logs --tail=100 postgres
```

O PostgreSQL grava no volume `book-vault-postgres-local_postgres-data`, montado em `/var/lib/postgresql`, conforme a imagem 18. O nome do projeto `book-vault-postgres-local` foi mantido para reutilizar o volume da migração. Não altere esse nome nem use outro `-p` em uma instalação existente sem planejar a mudança. O nome interno não determina o domínio público.

`compose.postgres.yaml` mantém a configuração do banco para preparação e diagnóstico. `compose.yaml` a reutiliza e adiciona a aplicação; use o Compose integrado na rotina. A API executa sem root, e os dois serviços têm verificações de disponibilidade e política de reinício. O Docker precisa estar funcionando; serviços parados manualmente não são ligados automaticamente por essa política.

| Configuração | Padrão | Uso |
| --- | --- | --- |
| `BIND_ADDRESS` | `127.0.0.1` | Interface do host que publica a porta no Compose. |
| `PORT` | `8000` | Porta publicada no host. |
| `POSTGRES_DB` | Definido em `.env.postgres` | Nome do banco PostgreSQL. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Definidos em `.env.postgres` | Credenciais locais, não versionadas. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `postgres` / `5432` no serviço da API | Destino interno da conexão; a senha original é tratada por `URL.create`. |
| `DATABASE_URL` | Opcional | URL explícita com prioridade sobre a configuração por campos. |
| `BOOK_VAULT_DB_PATH` | `book_vault.db` | Compatibilidade SQLite fora do Compose, quando não há URL nem host PostgreSQL. |

**Não inicie a biblioteca migrada pelo comando antigo do Uvicorn sem configurar a conexão.** Sem `DATABASE_URL` e sem `POSTGRES_HOST`, o código ainda utiliza SQLite por compatibilidade; os dois bancos não sincronizam. A execução pelo Compose configura PostgreSQL explicitamente.

Por padrão, o acesso fica restrito à máquina hospedeira. Para acessar a VPS por túnel SSH, execute no seu computador:

```bash
ssh -L 8080:127.0.0.1:8000 usuario@IP_DA_VPS
```

Com o túnel aberto, acesse `http://127.0.0.1:8080/` e `http://127.0.0.1:8080/docs`. Para domínio e HTTPS, configure o proxy e o controle de acesso conforme o ambiente. A aplicação ainda não possui autenticação: quem tiver acesso à API poderá alterar a biblioteca.

`docker compose down` preserva o volume. **Não use `docker compose down -v` se quiser manter os dados**, pois remove o volume. Mantenha o nome do projeto Compose ao atualizar para continuar utilizando o mesmo volume.

Consulte [o guia de implantação na VPS](docs/DEPLOY_VPS.md) para configuração, atualizações e backup com `pg_dump`. A imagem e os dois serviços foram construídos e verificados localmente; o funcionamento na VPS precisa ser validado no destino. O modelo local usa um administrador do PostgreSQL; uma implantação de produção deve planejar permissões limitadas para a aplicação. Alterar somente este README não exige reconstruir ou reiniciar os serviços.

## Estrutura principal

```text
frontend/           Interface web: HTML, CSS, JavaScript e imagem padrão
tests/              Testes automatizados
docs/DEPLOY_VPS.md   Hospedagem e backup
docs/POSTGRES_LOCAL.md PostgreSQL, migração e execução integrada
.github/workflows/  Testes automáticos no GitHub Actions
main.py             Aplicação FastAPI, rotas e entrega do frontend
models.py           Modelos SQLAlchemy e relacionamentos
schemas.py          Contratos de entrada, saída e validações
database.py         Conexões, sessões, preparo das tabelas e transações
migracao.py         Backup e transferência de SQLite para PostgreSQL
cadastro.py         Regras de cadastro de livros
edicao.py           Regras de edição de livros
autores.py          Gerenciamento de autores
catalogo.py         Catálogo fixo de gêneros
cliente_api.py      Cliente HTTP do menu
menu.py             Interface de terminal
Dockerfile          Imagem da aplicação
compose.yaml        Aplicação e PostgreSQL integrados
compose.postgres.yaml Configuração do serviço PostgreSQL e volume
.env.postgres.example Modelo de configuração sem credenciais reais
requirements.txt    Dependências Python
```

## Escopo e melhorias futuras

### Próxima funcionalidade aprovada: avaliações

**Planejada, ainda não implementada.** As regras foram aprovadas e registradas em [REQUISITOS.md](REQUISITOS.md); o endpoint e os componentes abaixo ainda não estão disponíveis.

- Avaliação opcional de **0,5 a 5,0**, em intervalos de **0,5**. Zero será rejeitado; `null` significará sem avaliação.
- Permitir adicionar ou editar a nota somente quando o status atual for **Lido** ou **Relendo**, com validação também no backend.
- Após cadastro como Lido ou Relendo, abrir um modal opcional com cinco estrelas clicáveis e seleção de meias estrelas, também acessível por teclado e com indicação numérica da nota.
- Após uma mudança de status para Lido ou Relendo, inclusive entre esses dois estados, oferecer o mesmo modal. Manter o mesmo status não caracteriza mudança.
- Se já existir avaliação, abrir o modal com a nota selecionada. Confirmar altera a nota; fechar ou escolher **Agora não** preserva a anterior. Sem nota anterior, mantém `null`.
- Cancelar a avaliação ou ocorrer uma falha nela não desfaz o cadastro ou a mudança de status já confirmados.
- Disponibilizar uma ação no card para adicionar ou editar avaliações de livros já cadastrados, respeitando os status permitidos. Livros existentes começarão sem nota.
- Preservar e exibir a avaliação se o status mudar para outro estado. Isso não libera adicionar ou editar a nota fora de Lido e Relendo.
- Permitir **Remover avaliação**, voltando a `null`, sem apagá-la automaticamente por mudança de status.

A implementação será dividida em pequenas etapas:

1. Adicionar o campo opcional `avaliacao` em `livros`, com decimal exato e restrições de intervalo e passo, preservando os registros existentes.
2. Criar schemas e a operação planejada `PATCH /livros/{livro_id}/avaliacao`, aceitando uma nota ou `null` para remoção; incluir o campo nas consultas.
3. Implementar o modal de estrelas e integrar as ações de cadastro, alteração de status e cards.
4. Testar valores inválidos, status elegíveis, preservação, remoção, livros antigos, cancelamento e falhas entre as operações.

### Outras possibilidades

Esta versão atende a uma biblioteca pessoal única. Autenticação, bibliotecas por usuário, histórico de releituras, diferenciação de autores homônimos, ISBN/edições e upload de imagens ficam como possibilidades de evolução, sem implementação nesta atualização.
