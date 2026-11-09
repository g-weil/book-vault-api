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
- Não implementar menu de terminal agora.
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

## Decisões ainda em aberto
- Se a obra terá campos adicionais (ano, ISBN, avaliação, notas); gêneros já foram aprovados como obrigatórios e múltiplos.
- Estratégia exata de criação/reutilização de autores homônimos.
- Se haverá histórico geral de mudanças de status e datas de leitura; o histórico detalhado de releituras já está reservado para uma versão futura.
- Desenho dos endpoints e schemas das funcionalidades posteriores ao cadastro e consulta iniciais.
- Como tratar versões/edições do mesmo título e usuários múltiplos.

## Critérios de desenvolvimento
Construção incremental; estudante implementa pequenos trechos e recebe explicação, revisão e testes. Não gerar aplicação inteira de forma automática.
