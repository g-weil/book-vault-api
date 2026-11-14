# Book Vault API — Contexto de produto e requisitos (versão inicial)

## Objetivo
API REST pessoal para organizar livros que a pessoa quer ler, está lendo, já leu, está relendo ou abandonou. Não é um inventário físico nem precisa controlar quantidades de exemplares.

## Stack planejada
Python, FastAPI, SQLAlchemy, SQLite, Pydantic. Sem frontend nesta primeira versão, testes manuais iniciais via documentação Swagger do FastAPI.

## Modelo de dados aprovado
- `autores`: cada autor possui um ID único e nome.
- `livros`: cada livro possui ID único, título e status de leitura.
- `livros_autores`: tabela associativa com `livro_id` e `autor_id`, permitindo relacionamento muitos-para-muitos (N:N). Impedir duplicação do mesmo par livro/autor.
- Um livro pode ter vários autores; um autor pode ter vários livros.
- `generos`: ID único e nome, com catálogo fixo definido abaixo.
- `livros_generos`: associação entre `livro_id` e `genero_id`, sem repetir o mesmo par. Um livro deve ter pelo menos um gênero e pode ter vários.
- Ao consultar um livro, retornar também os nomes de todos os autores.
- Ao consultar um autor, permitir obter os livros vinculados a ele.
- Exemplo: Good Omens — Neil Gaiman e Terry Pratchett (dois registros de autores, um registro de livro e dois vínculos).

## Regras de negócio
1. Ao cadastrar um livro, solicitar os autores e informar: "Se nenhum autor for informado, o livro será cadastrado como Autor desconhecido." Se nenhum nome for fornecido (inclusive entrada vazia ou somente espaços), vincular o livro a um único registro reutilizável chamado `Autor desconhecido`. Para cada autor informado, verificar se já existe pelo nome normalizado. Se existir, reutilizar seu ID e informar isso na resposta. Caso contrário, cadastrar o autor e vinculá-lo ao livro pelo respectivo ID.
2. Não permitir cadastrar o mesmo livro mais de uma vez na biblioteca pessoal. Ao identificar duplicidade, devolver os dados do livro existente, seu ID e status atual, com a mensagem: "Este livro já está cadastrado. Deseja alterar o status?" Sugestão de resposta HTTP 409 Conflict. Não alterar o status automaticamente: a alteração depende da decisão do usuário e será feita em uma operação separada. No Swagger, essa mensagem será apresentada na resposta; a API não abre uma pergunta interativa.
3. Para comparação de nomes e títulos, normalizar espaços e caixa (`" ".join(texto.split()).casefold()`). Na exibição dos títulos, preservar a capitalização enviada e normalizar os espaços (`" ".join(texto.split())`); para os nomes dos autores, preservar o texto original para exibição. Comparar livro por título normalizado + conjunto de IDs dos autores, independentemente da ordem dos autores, como regra inicial simplificada. Livros com o mesmo título e conjuntos de autores diferentes podem ser cadastrados separadamente, cada um vinculado aos respectivos IDs de autores. Homônimos, edições e ISBN serão refinados futuramente.
4. Cinco status permitidos: `Quero ler` (bookmark), `Lendo` (book-open), `Lido` (check-circle), `Relendo` (refresh-cw) e `Abandonado`. `Abandonado` significa que a pessoa começou a leitura e decidiu parar sem concluir. Qualquer outro status deve ser rejeitado, informando que a opção não existe e que é necessário escolher uma das cinco opções, exibidas na mensagem: "Status inválido: essa opção não existe. Escolha uma das opções: Quero ler, Lendo, Lido, Relendo ou Abandonado." As cinco opções também devem estar disponíveis na documentação Swagger/OpenAPI.
5. `Relendo` significa leitura novamente em andamento de livro já concluído. Na versão inicial, armazenar o estado atual; histórico detalhado de sessões de leitura é uma melhoria futura.
6. O escopo inicial é uma biblioteca pessoal única; se houver múltiplos usuários futuramente, a unicidade de livros deve ser avaliada por usuário, não globalmente.
7. O status é obrigatório no cadastro, sem valor padrão. Exibir as cinco opções para o usuário escolher: `Quero ler`, `Lendo`, `Lido`, `Relendo` e `Abandonado`. No Swagger/OpenAPI, documentar as opções permitidas e a obrigatoriedade do campo, assim como o aviso sobre autor não informado.
8. O usuário escolhe um ou mais gêneros principais do catálogo fixo; não pode cadastrar novos gêneros. Os subgêneros entre parênteses são orientações de escolha, não registros separados.
9. A consulta da biblioteca deve incluir os autores e gêneros de cada livro. Se estiver vazia, retornar a mensagem `Sua biblioteca está vazia` e uma lista `livros` vazia.

## Catálogo aprovado de gêneros
- Fantasia (alta fantasia, fantasia urbana, fantasia sombria, realismo mágico).
- Ficção científica (distopia, cyberpunk, viagens no tempo, exploração espacial).
- Mistério e suspense (policial, investigação, espionagem, suspense psicológico).
- Terror (sobrenatural, psicológico, gótico).
- Romance amoroso (contemporâneo, histórico, comédia romântica).
- Ficção geral (drama, aventura, humor, ficção histórica, ficção contemporânea).
- Poesia e textos breves (poesia, contos, crônicas).
- Teatro (tragédia, comédia, drama teatral).
- Quadrinhos (HQ, mangá, graphic novel).
- Biografias e memórias (biografia, autobiografia, diários, relatos pessoais).
- História e sociedade (história, política, sociologia, antropologia).
- Filosofia e espiritualidade (filosofia, religião, teologia, espiritualidade).
- Ciência e tecnologia (ciências naturais, matemática, computação, engenharia).
- Desenvolvimento pessoal e saúde (autoajuda, psicologia, bem-estar, saúde).
- Educação e estudos (pedagogia, idiomas, materiais didáticos).
- Negócios e economia (administração, empreendedorismo, finanças, economia).
- Artes e cultura (música, cinema, fotografia, arquitetura, crítica cultural).
- Interesses e vida prática (culinária, viagens, esportes, jardinagem, hobbies).

## Primeira etapa da API
- Implementar cadastro (`POST /livros`) e consulta da biblioteca (`GET /livros`) em pequenas etapas, com verificação antes de avançar às demais funcionalidades.
- Disponibilizar o catálogo para consulta em `GET /generos` para orientar a seleção de IDs no cadastro.
- A primeira etapa foi concluída e integrada à main; o menu de terminal passa a consumir esses endpoints na etapa seguinte.
- `POST /livros` retorna HTTP 201 com `mensagem`, `livro` (ID, título, autores, gêneros e status) e `autores_reutilizados` (ID e nome dos autores existentes usados no cadastro).
- IDs de gêneros inexistentes retornam HTTP 422, com mensagem e lista dos IDs não encontrados. Repetições de gênero ou do mesmo nome normalizado de autor no pedido geram apenas um vínculo.
- Livro duplicado retorna HTTP 409 com `detail.mensagem` e `detail.livro`, incluindo ID e status atuais. Não altera o livro existente.
- O cadastro é transacional: autores novos, livro e vínculos são confirmados juntos. Erros desfazem as alterações. No SQLite, os cadastros são serializados com `BEGIN IMMEDIATE` antes da verificação de duplicidade.

## Consulta de autores e busca de livros por autor
- `GET /autores` retorna HTTP 200 com uma lista de objetos `AutorConsulta` (ID e nome), ordenados por ID, incluindo autores sem livros e `Autor desconhecido` caso cadastrado.
- O parâmetro opcional `nome` permite busca parcial pelo nome normalizado, sem diferenciar maiúsculas/minúsculas e normalizando espaços com `casefold()`. Caracteres como `%` e `_` são tratados como texto literal. Não há remoção de acentos.
- Sem filtro, listar todos os autores. Sem resultados, retornar HTTP 200 com `[]`. Filtro enviado vazio ou somente com espaços retorna HTTP 422; para listar todos, omitir o parâmetro.
- `GET /livros` aceita `autor_id` (inteiro positivo) ou `autor_nome` (busca parcial com as mesmas regras de normalização e caracteres literais de `GET /autores`). Enviar ambos, ID inválido ou nome vazio/somente espaços retorna HTTP 422.
- Sem livros para o filtro, retornar HTTP 200, lista vazia e a mensagem `Nenhum livro encontrado para esse autor`, inclusive para ID de autor inexistente. Sem filtro, preservar a consulta geral da biblioteca e sua mensagem de biblioteca vazia.
- Cada livro aparece uma única vez, mesmo quando vários de seus autores correspondem ao trecho pesquisado. A resposta inclui todos os autores e gêneros de cada livro encontrado, não apenas os autores que corresponderam ao filtro.
- O menu/frontend pode reunir listagem e busca em uma só interação: digitar parte do nome, selecionar um autor encontrado e consultar seus livros pelo ID.

## Exclusão de livros
- `DELETE /livros/{livro_id}` exclui definitivamente o livro e seus vínculos em `livros_autores` e `livros_generos`, em uma única transação.
- Os autores e gêneros continuam cadastrados, mesmo que fiquem sem livros; vínculos de outros livros são preservados.
- Sucesso retorna HTTP 204 sem corpo. Livro inexistente, inclusive após já ter sido excluído, retorna HTTP 404 com `Livro não encontrado.`. ID não positivo ou inválido retorna HTTP 422.
- A confirmação da exclusão será responsabilidade do futuro menu/frontend; o endpoint executa a exclusão ao receber a requisição válida.

## Gerenciamento de autores
- `POST /autores` recebe `nome` obrigatório e não vazio. Retorna HTTP 201 com ID e nome; se o nome normalizado já existir, retorna HTTP 409 com mensagem e os dados do autor existente em `detail.autor`.
- `PATCH /autores/{autor_id}` recebe `nome` obrigatório, corrige o registro mantendo seu ID e retorna HTTP 200. A correção aparece em todos os livros vinculados. Nome normalizado pertencente a outro autor retorna HTTP 409; não há união automática de registros. Manter o próprio nome ou corrigir sua capitalização é permitido.
- `DELETE /autores/{autor_id}` exclui apenas autor sem livros vinculados. Sucesso retorna HTTP 204 sem corpo; se houver vínculo, retorna HTTP 409 e preserva autor, livros e vínculos.
- Edição e exclusão de autor inexistente retornam HTTP 404. IDs não positivos, nomes vazios, campos ausentes ou adicionais retornam HTTP 422.
- `AutorCadastro` e `AutorEdicao` compartilham validação de nome, preservando o texto enviado para exibição e usando normalização de espaços e `casefold()` na comparação. As operações são transacionais.

## Edição de título, autores e gêneros
- `PATCH /livros/{livro_id}` recebe os campos opcionais `titulo`, `autores` e `genero_ids`. Campos omitidos preservam os valores atuais; `null` explícito e campos adicionais são rejeitados com HTTP 422. Um objeto vazio não altera o livro e retorna os dados atuais.
- Título informado deve ser não vazio, preservando a capitalização e normalizando os espaços.
- Autores informados substituem o conjunto atual, reutilizando os IDs existentes e criando apenas autores novos. Lista vazia ou contendo somente nomes em branco preserva os autores atuais, sem atribuir `Autor desconhecido`. Essa regra é específica da edição; no cadastro, a ausência de autores continua vinculando `Autor desconhecido`.
- Autores removidos dos vínculos continuam cadastrados. Gêneros enviados substituem o conjunto atual, devem existir no catálogo e conter ao menos um ID; repetições geram um único vínculo.
- A combinação final de título normalizado e conjunto de autores não pode duplicar outro livro, desconsiderando o próprio registro. Conflito retorna HTTP 409 com os dados do outro livro e desfaz toda a edição.
- Sucesso retorna HTTP 200 com `LivroConsulta`; livro inexistente retorna HTTP 404. A edição é transacional e preserva o status, que continua sendo alterado pelo endpoint específico. O schema é `LivroEdicao`.

## Alteração do status de leitura
- `PATCH /livros/{livro_id}/status` recebe apenas `status`, obrigatório entre as cinco opções aprovadas. Campos adicionais são rejeitados com HTTP 422.
- O ID deve ser um inteiro positivo. Livro inexistente retorna HTTP 404 com `detail` igual a `Livro não encontrado.`; entrada inválida retorna HTTP 422.
- O sucesso retorna HTTP 200 com os dados de `LivroConsulta` após confirmar a transação. Somente o status é alterado; repetir o status atual também é aceito.
- `EntradaStatus` reúne a validação compartilhada de status; `LivroCadastro` e `LivroStatusAlteracao` herdam essa validação. Não é criado histórico de leitura nesta etapa.

## Schemas da primeira etapa
- `LivroCadastro`: recebe `titulo`, `autores` (lista de nomes, opcional), `genero_ids` (lista obrigatória com pelo menos um inteiro positivo) e `status` obrigatório. O ID do livro é gerado pelo banco; campos normalizados são calculados internamente.
- O título tem espaços normalizados e não pode ficar vazio. A capitalização é preservada. O status rejeita valores fora das cinco opções com a mensagem definida nas regras de negócio.
- No cadastro de livro, nomes de autores vazios ou compostos apenas por espaços são desconsiderados. Se não restar nenhum nome, a lógica de cadastro deve vincular `Autor desconhecido`. O schema não cria registros no banco.
- `AutorCadastro`: define nome obrigatório e não vazio para cadastro direto de autores. `AutorEdicao` herda essa validação. Isso não altera a possibilidade de omitir autores no cadastro de livro.
- `AutorConsulta` e `GeneroConsulta`: retornam ID e nome. Não há schema para cadastrar gêneros, pois o catálogo é fixo.
- `LivroConsulta`: retorna ID, título, status, autores e gêneros, estes como listas de objetos com ID e nome. Aceita leitura dos atributos de modelos SQLAlchemy.
- `BibliotecaConsulta`: retorna `mensagem` e `livros`; a lógica de consulta deve produzir `Sua biblioteca está vazia` quando a lista estiver vazia.
- A existência dos IDs de gêneros, a reutilização de autores, a normalização com `casefold()` para comparação e a detecção de livros duplicados precisam de lógica de cadastro e consulta ao banco; não são garantidas apenas pelos schemas.
- Estes schemas não implementam endpoints nem operações no banco. Os schemas das demais funcionalidades serão definidos nas respectivas etapas.

## Exemplo de resposta de consulta
```json
{
  "id": 10,
  "titulo": "Good Omens",
  "autores": [
    {"id": 1, "nome": "Neil Gaiman"},
    {"id": 2, "nome": "Terry Pratchett"}
  ],
  "status": "Quero ler",
  "generos": [
    {"id": 1, "nome": "Fantasia"}
  ]
}
```

## Menu de terminal
- `menu.py` é um cliente HTTP da API em `http://127.0.0.1:8000`, utilizando a biblioteca padrão do Python. Não acessa o SQLite diretamente. O servidor deve ser iniciado em outro terminal.
- Opções: 1 cadastrar livro; 2 consultar biblioteca; 3 buscar livros por autor; 4 alterar status; 5 gerenciar autores; 6 excluir livro; 7 editar título/autores/gêneros; 0 sair.
- O cadastro exibe o catálogo antes de pedir os IDs de gêneros e as cinco opções antes de escolher o status. Vários autores são separados por ponto e vírgula; gêneros por vírgula. Autor em branco é enviado como lista vazia, para a API atribuir Autor desconhecido.
- Ao receber livro duplicado, mostrar o livro existente e perguntar se deseja alterar seu status, realizando o PATCH apenas após confirmação e escolha do status.
- A busca por autor recebe parte do nome, mostra os autores encontrados e permite selecionar o ID para consultar os livros. Campo de busca vazio lista todos os autores.
- Na edição de livro, entradas em branco preservam os valores; listas preenchidas substituem os vínculos atuais. Alterações e exclusões têm confirmação. Gêneros continuam obrigatórios; não é possível remover todos.
- Gerenciamento de autores oferece consulta, cadastro, edição de nome e exclusão. O menu informa que renomear afeta todos os livros e exibe as recusas da API, incluindo exclusão de autor com vínculos.
- `0` volta nas seleções de ID/status ou cancela a seleção de gêneros. Falhas de conexão e erros da API devem ser apresentados em texto, sem encerrar o menu nem repetir automaticamente operações de escrita.

## Frontend web — desenvolvimento incremental
- HTML, CSS e JavaScript puro, sem framework nem dependências adicionais. Arquivos em `frontend/`, servidos pelo próprio FastAPI: página em `/`, assets em `/static` e Swagger em `/docs`. Uso local nesta etapa, sem publicação.
- Tema escuro, biblioteca em cards e formulários em modais. As funcionalidades do menu serão integradas progressivamente; já oferece consulta dos livros, filtro visual por status, edição da URL da capa e cadastro de livros em modal.
- O modal de cadastro carrega `GET /generos` e exibe os nomes em caixas de seleção, exigindo ao menos uma. Apresenta os cinco status, com escolha obrigatória e sem valor padrão. Autores são opcionais e separados por ponto e vírgula; capa também é opcional. Envia JSON ao `POST /livros`, exibe os autores reutilizados e insere o card retornado na estante, sem recarregar a página.
- Durante o envio, bloquear novos envios e fechamento do modal. Erros preservam os campos; falha ao carregar gêneros bloqueia o cadastro e permite tentar novamente.
- Duplicidade continua sendo identificada pelo título normalizado e conjunto de autores. Se o status enviado for igual ao atual, API, menu e frontend informam `Este livro já está cadastrado e já possui esse mesmo status.`. A API mantém HTTP 409; menu e frontend não oferecem alteração nem enviam PATCH nesse caso.
- Se o status for diferente, a duplicidade HTTP 409 mostra o livro e o status atuais, oferecendo confirmar a alteração para o status escolhido. Apenas a confirmação envia `PATCH /livros/{id}/status`; recusar fecha sem alterar nada. Demais campos e capa do cadastro existente são preservados.
- `capa_url` é opcional em livros, cadastro, edição e consulta. Armazena somente uma URL HTTP/HTTPS, não o arquivo da imagem. Campos omitidos na edição preservam o link; texto vazio ou `null` remove a capa. URLs inválidas retornam HTTP 422. A capa não participa da regra de duplicidade.
- Livros existentes recebem `capa_url = NULL` por alteração aditiva de tabela na inicialização, sem apagar registros. A alteração pode ser executada novamente sem duplicar a coluna.
- O navegador carrega a imagem diretamente do endereço externo; se não houver link ou houver falha no carregamento, mostra uma capa padrão. O backend não baixa imagens externas.
- Usar estrutura HTML semântica, textos em português, campos rotulados, navegação por teclado, layout adaptável ao celular e mensagens de carregamento, erro e biblioteca vazia.
- Cada card oferece `Editar livro`, reaproveitando o formulário em modo edição com título, autores, gêneros atuais marcados e capa preenchidos. O status fica fora desse formulário e é preservado.
- A edição envia apenas os campos alterados para `PATCH /livros/{id}`. Autores em branco preservam os atuais; gêneros exigem ao menos uma seleção e substituem o conjunto atual; capa em branco remove a imagem. Sem mudanças, informar `Nenhuma alteração informada.` sem enviar requisição.
- Sucesso atualiza o card sem recarregar a página e mantém o filtro de status. Erros, inclusive conflito HTTP 409, mantêm os campos preenchidos e não oferecem alteração de status nesse fluxo. Cancelar fecha sem salvar. Durante o envio, bloquear envios repetidos e fechamento do modal.
- O card apresenta `Atualizar status` entre `Editar livro` e `Editar capa`, como texto verde sem fundo. O modal mostra o livro e as cinco opções com o status atual selecionado. Manter o mesmo status informa que não houve alteração, sem enviar PATCH.
- Confirmar outro status envia `PATCH /livros/{id}/status`, atualiza o card e preserva o filtro atual. Se o livro não corresponder mais ao filtro, deixa de ser exibido. Cancelar não salva; erros preservam a seleção. Bloquear envios duplicados e fechamento durante a requisição.
- Cada card oferece `Excluir livro`, que abre confirmação com título e autores, informando a exclusão definitiva e a preservação dos cadastros de autores e gêneros. Cancelar não envia requisição; confirmar envia `DELETE /livros/{id}`.
- Após HTTP 204, remover o card da memória e da tela, atualizar a contagem e preservar o filtro ativo. Tratar 204 sem tentar converter corpo vazio em JSON. Erros mantêm o modal e a mensagem da API; durante o envio, bloquear confirmação repetida e fechamento. Em falha de conexão, orientar a atualizar a biblioteca antes de tentar novamente, pois o resultado da operação pode ser incerto.
- A barra lateral permite alternar `Biblioteca` e `Autores`, usando a mesma área central sem abrir outra página. A área ativa é destacada e o cabeçalho acompanha a seleção.
- Na área Autores, consultar `GET /autores` e exibir nomes e IDs em tabela, incluindo autores sem vínculos. A busca por parte do nome envia `GET /autores?nome=...` ao clicar em Buscar ou pressionar Enter. Campo vazio/somente espaços omite o filtro; Mostrar todos limpa a busca. Atualizar repete a consulta atual.
- Mostrar quantidade de resultados, carregamento, ausência de autores/resultados e falhas de conexão. Somente a resposta da consulta mais recente deve ser exibida.
- A área Autores oferece `Cadastrar autor` e `Editar` em cada linha, usando um modal com nome obrigatório. Cadastro envia `POST /autores`; edição abre preenchida e envia `PATCH /autores/{id}`. Informar que renomear afeta todos os livros vinculados, mantendo ID e vínculos.
- Nome em branco é rejeitado. Edição sem mudança informa que não houve alteração sem enviar PATCH. Conflitos HTTP 409 exibem a mensagem e o ID/nome do autor existente, mantendo o formulário preenchido; não unir registros automaticamente. Cancelar não salva; bloquear envios repetidos e fechamento durante a requisição.
- Após salvar, limpar o filtro de autores, atualizar a tabela e exibir confirmação. Renomear também atualiza os autores nos livros já carregados na memória do frontend.
- A tabela de autores oferece `Excluir` ao lado de `Editar`. Abrir confirmação com ID e nome, avisando que a exclusão é definitiva e só é permitida sem livros vinculados. Cancelar não envia requisição; confirmar envia `DELETE /autores/{id}`.
- HTTP 204 fecha a confirmação, reconsulta a tabela mantendo a busca e atualiza a contagem. HTTP 409 mostra a mensagem de bloqueio e mantém o autor e o modal; demais erros também são exibidos sem remover registros da tela. Bloquear envios repetidos e fechamento durante a requisição. Nenhum livro é excluído nesse fluxo.
- A biblioteca oferece busca de autor por parte do nome, carregando sugestões de `GET /autores?nome=...` ao digitar (com intervalo de 300 ms) ou enviar a busca. Sugestões são botões selecionáveis por teclado, com nome e ID; selecionar consulta `GET /livros?autor_id=...` e destaca o autor ativo. Nunca enviar nome e ID juntos.
- O filtro de status é aplicado localmente sobre os livros do autor selecionado, mantendo todos os coautores na resposta/card e sem repetir livros. Atualizar e voltar à biblioteca preservam o autor e o status selecionados. Edição dos vínculos e alteração de status atualizam a lista respeitando os dois filtros.
- Limpar busca (ou enviar termo vazio) remove somente o filtro de autor e reconsulta a biblioteca, mantendo o status. Mostrar mensagens distintas para autor sem livros, combinação autor/status sem resultados e busca sem autores encontrados. Respostas antigas não devem substituir consultas mais recentes.
- Ao concluir um novo cadastro ou o fluxo de status após cadastro duplicado, limpar os filtros para mostrar o livro salvo e recarregar a biblioteca completa se antes havia filtro de autor. Ao renomear o autor selecionado, atualizar também o rótulo do filtro.
- Acima da busca por autor, oferecer busca por título com atualização após 300 ms de digitação ou envio do formulário. Acrescentar o parâmetro opcional `titulo` ao `GET /livros`: comparação parcial por espaços normalizados e `casefold()`, preservando a exibição original e tratando `%`/`_` como texto literal. Pode combinar com o filtro de autor; vazio explícito retorna HTTP 422 e deve ser omitido pela interface.
- Os cards e sugestões de volumes respeitam título, autor e status. As sugestões mostram título, autores e ID; selecionar restringe a tela a esse ID para distinguir títulos iguais com autorias diferentes. Atualizar preserva a seleção e os filtros. Editar o título do livro selecionado atualiza o campo e o rótulo sem trocar seu ID.
- `Limpar título` remove apenas título/seleção de livro, preservando autor e status. Limpar autor também preserva o título. Buscas por título sem resultados retornam HTTP 200 com lista vazia e a interface explica os filtros. Novos cadastros limpam todos os filtros e recarregam os livros se antes havia filtro de autor ou título.
- Na biblioteca, as buscas de título e autor não têm botões de buscar: as sugestões são automáticas ao digitar, e Enter executa imediatamente. Manter rótulos, mensagens de carregamento/erro, botões de limpar e seleção de sugestões por teclado. Essa mudança não remove o botão Buscar da área de gerenciamento de autores.

## Execução em VPS com Docker
- Dockerfile com Python 3.12, API e frontend no mesmo contêiner, um processo Uvicorn sem reload e usuário sem privilégios de root.
- `BOOK_VAULT_DB_PATH` permite configurar o arquivo SQLite; sem a variável, preservar o caminho local anterior. No Docker, usar `/data/book_vault.db` em volume persistente gerenciado pelo Compose.
- Não copiar banco local, ambiente virtual, credenciais ou testes para a imagem. O primeiro início usa banco novo e carrega os gêneros. A importação de dados locais é uma etapa separada.
- Porta publicada somente em 127.0.0.1 por padrão. Acesso inicial por túnel SSH ou proxy com controle de acesso, pois a API atual não tem autenticação. Publicação, domínio e importação não são executados nesta preparação.
- Incluir healthcheck, reinício após encerramento do processo, rotação de logs e instruções de atualização, parada e backup consistente do SQLite em `docs/DEPLOY_VPS.md`.

## Migração para PostgreSQL — preparação local
- Etapa 1: `database.py` aceita `DATABASE_URL` e usa Psycopg 3 para PostgreSQL. Sem a variável, preservar SQLite e `BOOK_VAULT_DB_PATH`. Aplicar opções e PRAGMA do SQLite somente à conexão SQLite.
- Etapa 1 concluída: conexão TCP PostgreSQL autenticada, sem transferência de registros.
- Etapa 2: criação e inspeção das tabelas compatíveis com PostgreSQL e SQLite. Preservar a alteração aditiva de capa para bancos anteriores; `create_all` não substitui migrações versionadas.
- Centralizar escritas em `transacao_escrita`: `BEGIN IMMEDIATE` no SQLite e bloqueio transacional consultivo comum no PostgreSQL (`pg_advisory_xact_lock`, isolamento `READ COMMITTED`), antes das consultas de validação. Aplicar também a alterações de status e carga inicial de gêneros. O bloqueio é cooperativo entre as operações da aplicação, não uma restrição única para escritas SQL externas.
- Validar os fluxos HTTP, terminal e frontend com PostgreSQL em banco temporário exclusivo dos testes; incluir cadastros e edições simultâneos, rollback e inicialização repetida. Manter o banco padrão da biblioteca em SQLite até backup, transferência e conferência.
- Migração aprovada de forma incremental, preservando os dados e as regras existentes.
- Primeiro preparar PostgreSQL 18 pelo Docker Desktop, em `compose.postgres.yaml`, separado da aplicação atual, com volume persistente e porta publicada somente em 127.0.0.1.
- Credenciais locais em `.env.postgres`, ignorado pelo Git; disponibilizar somente o modelo sem credenciais reais.
- Etapa 3 concluída: `migracao.py` gera backup SQLite consistente, bloqueia escritas na origem durante a operação e copia para PostgreSQL vazio em transação única. Recusar destino preenchido, sem sobrescrever ou mesclar registros; preservar o SQLite original e o backup em caso de erro.
- Comparar integralmente campos e vínculos antes do commit e ajustar as sequências de IDs por reinício transacional. Validar também após o commit e a inicialização da API. Foram preservados 6 livros, 5 autores, 18 gêneros, 6 vínculos de autoria e 9 vínculos de gênero na transferência local.
- Etapa 4: Compose integrado com dois serviços (`book-vault` e `postgres`), reutilizando o projeto e volume existentes da migração. API aguarda o banco healthy e acessa `postgres:5432`, com configuração explícita via `POSTGRES_HOST` e campos de `.env.postgres`, sem concatenar senha em URL. `DATABASE_URL` continua tendo prioridade; sem URL e sem host, manter compatibilidade SQLite, sem retomar gravações no banco antigo.
- Dockerfile da aplicação sem armazenamento SQLite em `/data`; dados do PostgreSQL somente no volume do banco. Excluir backups e dumps da imagem e do Git. Início pelo Compose não depende de variáveis temporárias do terminal.
- Guia da VPS adaptado para PostgreSQL e backup via pg_dump. Workflow de CI configurado com PostgreSQL 18 temporário, healthcheck, conexão explícita de teste e suíte SQLite/PostgreSQL/menu/frontend/transferência. Credenciais apenas do serviço descartável, sem acesso ao banco pessoal. Conferir execução remota após commit e push; falta atualização final do README.
- Na transferência, preservar IDs e vínculos das cinco tabelas, ajustar os geradores de IDs e validar os dados antes de trocar o banco utilizado pela API.
- Instruções de uso e persistência em `docs/POSTGRES_LOCAL.md`.

## Avaliação de livros — aprovada, implementação após a migração
- Implementar somente após concluir e validar a migração para PostgreSQL. Esta seção registra o planejamento; a funcionalidade ainda não está disponível.
- Cada livro poderá ter uma avaliação atual opcional: 0,5; 1,0; 1,5; 2,0; 2,5; 3,0; 3,5; 4,0; 4,5 ou 5,0. Zero não será aceito; `null` representa ausência de avaliação.
- Permitir adicionar ou editar a avaliação somente quando o status atual for `Lido` ou `Relendo`, pois é necessário ter concluído uma leitura. Validar essa regra também no backend.
- Ao cadastrar diretamente como `Lido` ou `Relendo`, após o sucesso abrir um modal opcional de avaliação. Fechar, cancelar ou escolher `Agora não` mantém o cadastro e não grava uma nota.
- Ao mudar de outro status para `Lido` ou `Relendo`, inclusive de `Lido` para `Relendo` e vice-versa, após o sucesso oferecer o mesmo modal. Manter o mesmo status não caracteriza mudança.
- O modal terá cinco estrelas clicáveis com seleção de meias estrelas, permitindo as dez notas. Também deverá permitir seleção por teclado e informar a nota numericamente.
- Quando existir avaliação, abrir o modal com a nota atual selecionada. Salvar altera a nota; dispensar mantém a avaliação anterior. Falha ao avaliar não desfaz o cadastro ou a mudança de status já confirmados.
- Oferecer uma ação no card para avaliar livros já cadastrados e editar a avaliação, respeitando os status permitidos. Livros existentes começarão sem avaliação.
- Preservar e exibir a nota quando o livro mudar para outro status. Essa preservação não libera adicionar ou editar avaliações fora de `Lido` e `Relendo`.
- Permitir remover explicitamente a avaliação, voltando a `null`; não remover a nota automaticamente por mudança de status.
- Planejamento técnico: campo opcional `avaliacao` na tabela `livros`, com representação decimal exata e restrições de intervalo e passo no schema e no banco; operação específica `PATCH /livros/{livro_id}/avaliacao`, separada do cadastro e da alteração de status, aceitando nota ou `null` para remoção; incluir o campo nas consultas.
- Testar limites e meias estrelas, rejeição de zero e notas intermediárias inválidas, status elegíveis, preservação e remoção, livros antigos, cancelamento do modal e falhas após cadastro/alteração de status.

## Estrutura Docker aprovada após a migração
- Dois serviços: aplicação (FastAPI e arquivos estáticos do frontend) e PostgreSQL, em contêineres separados conectados pela rede do Compose.
- Volume persistente exclusivo do PostgreSQL; atualizar a imagem da aplicação não exige recriar o banco.
- Não separar o frontend em um terceiro contêiner nesta etapa. O Compose atual com SQLite será adaptado após a validação da migração; a configuração local do PostgreSQL permanece separada durante a preparação.

## Decisões ainda em aberto
- Se a obra terá campos adicionais (ano, ISBN, notas textuais); avaliação foi aprovada acima para implementação posterior à migração, e gêneros já são obrigatórios e múltiplos.
- Estratégia exata de criação/reutilização de autores homônimos.
- Se haverá histórico geral de mudanças de status e datas de leitura; o histórico detalhado de releituras já está reservado para uma versão futura.
- Desenho dos endpoints e schemas das funcionalidades posteriores ao cadastro e consulta iniciais.
- Como tratar versões/edições do mesmo título e usuários múltiplos.

## Critérios de desenvolvimento
Construção incremental; estudante implementa pequenos trechos e recebe explicação, revisão e testes. Não gerar aplicação inteira de forma automática.
