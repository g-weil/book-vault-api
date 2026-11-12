# Book Vault API

Biblioteca pessoal para organizar livros, autores, gêneros e o andamento das leituras. Projeto de estudo e portfólio com API REST, interface web e menu de terminal.

## Funcionalidades e tecnologias

- Cadastro, consulta, edição e exclusão de livros e autores.
- Biblioteca em cards, capas opcionais e formulários em modais.
- Busca por título e autor, combinada com filtro de status.
- Vários autores e gêneros por livro, com catálogo fixo de 18 gêneros.
- Cinco status: **Quero ler**, **Lendo**, **Lido**, **Relendo** e **Abandonado**.
- Validação de dados, prevenção de duplicidades e persistência em SQLite.
- Configuração Docker para hospedagem em VPS.

| Camada | Tecnologias |
| --- | --- |
| API | Python, FastAPI e Uvicorn |
| Modelagem e validação | SQLAlchemy e Pydantic |
| Banco | SQLite |
| Interface web | HTML, CSS e JavaScript puro |
| Testes | unittest, HTTP e JavaScript com Node.js |
| Implantação | Docker e Docker Compose |

## Executar localmente

Use Python 3.12, versão utilizada no desenvolvimento. Não é necessário instalar SQLite separadamente nem instalar Node.js para usar a aplicação.

```bash
git clone https://github.com/g-weil/book-vault-api.git
cd book-vault-api
```

No Windows, pelo PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

No Linux ou macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn main:app --reload
```

Mantenha esse terminal aberto enquanto utiliza a aplicação.

| Acesso | Endereço |
| --- | --- |
| Interface web | http://127.0.0.1:8000/ |
| Swagger | http://127.0.0.1:8000/docs |
| OpenAPI | http://127.0.0.1:8000/openapi.json |

A API serve também a interface web; não é necessário iniciar outro servidor para o frontend. Na inicialização, prepara as tabelas e o catálogo de gêneros. Por padrão, os dados ficam em `book_vault.db`, na pasta do projeto. O banco local e o ambiente virtual não são versionados.

Se aparecer `ERR_CONNECTION_REFUSED`, confira se o Uvicorn continua em execução. Atualizar a página não inicia o servidor.

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

Com a API em execução, abra um segundo terminal na pasta do projeto.

Windows:

```powershell
.\.venv\Scripts\python.exe menu.py
```

Linux ou macOS:

```bash
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

- `livros`: título, título normalizado, status e URL opcional da capa.
- `autores`: nome e nome normalizado, com unicidade do nome normalizado.
- `generos`: catálogo fixo, sem cadastro livre pelo usuário.
- `livros_autores` e `livros_generos`: relações muitos-para-muitos, sem repetição do mesmo par de IDs.
- A identidade do livro considera título normalizado e conjunto de autores; status, capa e gêneros não definem duplicidade.
- Escritas são transacionais: alterações relacionadas são confirmadas juntas ou desfeitas em caso de erro.

As decisões detalhadas estão em [REQUISITOS.md](REQUISITOS.md). A inicialização também trata a adição da coluna de capa em bancos da versão anterior; isso não substitui um sistema geral de migrações.

## Testes

### Execução automática no GitHub

O workflow [Testes automatizados](.github/workflows/testes.yml) executa a suíte a cada `push` e `pull request`. Também pode ser iniciado manualmente pela aba **Actions**, em **Run workflow**, quando o arquivo estiver na branch padrão.

O GitHub prepara um ambiente Linux com Python 3.12 e Node.js 24, instala as dependências e executa os testes existentes. Node.js é instalado para que o teste do JavaScript não seja ignorado. Os bancos de teste são isolados; o workflow não acessa a VPS nem faz implantação.

Após enviar as alterações, abra a aba **Actions** ou os checks da pull request. Uma execução verde indica sucesso; em caso de falha, abra a etapa **Executar testes** para consultar os detalhes. Para impedir merges com testes falhando, é necessário configurar uma regra de proteção da branch exigindo o check **API, menu e frontend**.

### Execução local

Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Linux ou macOS:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

Os testes utilizam banco em memória ou arquivos temporários, sem modificar a biblioteca local. Verificam operações por HTTP, fluxos do menu e preparação/persistência do banco.

Se Node.js estiver disponível, a suíte também verifica interações do JavaScript com um DOM simplificado e requisições reais à API temporária. Isso não substitui testes visuais e de interação em um navegador. Node.js não é necessário para executar a aplicação.

Para uma verificação manual, cadastre um livro de teste, localize-o pelos filtros, altere o status, edite os dados e exclua-o. Confira que o autor permanece cadastrado e só pode ser excluído quando não tiver outros livros vinculados.

## Docker e VPS

Com Docker e Docker Compose instalados, execute na raiz:

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 book-vault
```

API e frontend ficam no mesmo contêiner. O SQLite fica em `/data/book_vault.db`, no volume persistente `book-vault-data`. O banco local não é copiado para a imagem: uma instalação nova começa com uma biblioteca vazia.

| Configuração | Padrão | Uso |
| --- | --- | --- |
| `BIND_ADDRESS` | `127.0.0.1` | Interface do host que publica a porta no Compose. |
| `PORT` | `8000` | Porta publicada no host. |
| `BOOK_VAULT_DB_PATH` | `book_vault.db` local; `/data/book_vault.db` no contêiner | Caminho do banco usado pela aplicação. |

Por padrão, o acesso fica restrito à máquina hospedeira. Para acessar a VPS por túnel SSH, execute no seu computador:

```bash
ssh -L 8080:127.0.0.1:8000 usuario@IP_DA_VPS
```

Com o túnel aberto, acesse `http://127.0.0.1:8080/` e `http://127.0.0.1:8080/docs`. Para domínio e HTTPS, configure o proxy e o controle de acesso conforme o ambiente. A aplicação ainda não possui autenticação: quem tiver acesso à API poderá alterar a biblioteca.

`docker compose down` preserva o volume. **Não use `docker compose down -v` se quiser manter os dados**, pois remove o volume. Mantenha o nome do projeto Compose ao atualizar para continuar utilizando o mesmo volume.

Consulte [o guia de implantação na VPS](docs/DEPLOY_VPS.md) para atualizações, verificação do serviço e backups. A construção da imagem e a execução na VPS precisam ser conferidas no ambiente de destino. Alterar somente este README não exige reconstruir ou reiniciar a aplicação.

## Estrutura principal

```text
frontend/           Interface web: HTML, CSS, JavaScript e imagem padrão
tests/              Testes automatizados
docs/DEPLOY_VPS.md   Hospedagem e backup
main.py             Aplicação FastAPI, rotas e entrega do frontend
models.py           Modelos SQLAlchemy e relacionamentos
schemas.py          Contratos de entrada, saída e validações
database.py         Conexão, sessões e preparação do SQLite
cadastro.py         Regras de cadastro de livros
edicao.py           Regras de edição de livros
autores.py          Gerenciamento de autores
catalogo.py         Catálogo fixo de gêneros
cliente_api.py      Cliente HTTP do menu
menu.py             Interface de terminal
Dockerfile          Imagem da aplicação
compose.yaml        Serviço e volume persistente
requirements.txt    Dependências Python
```

## Escopo e melhorias futuras

Esta versão atende a uma biblioteca pessoal única. Autenticação, bibliotecas por usuário, histórico de releituras, diferenciação de autores homônimos, ISBN/edições e upload de imagens ficam como possibilidades de evolução.
