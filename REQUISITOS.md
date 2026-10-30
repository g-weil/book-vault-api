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

## Exemplo de resposta de consulta
```json
{
  "id": 10,
  "titulo": "Good Omens",
  "autores": [
    {"id": 1, "nome": "Neil Gaiman"},
    {"id": 2, "nome": "Terry Pratchett"}
  ],
  "status": "Quero ler"
}
```

## Decisões ainda em aberto
- Se a obra terá campos adicionais (ano, ISBN, avaliação, notas); gêneros já foram aprovados como obrigatórios e múltiplos.
- Estratégia exata de criação/reutilização de autores homônimos.
- Se haverá histórico geral de mudanças de status e datas de leitura; o histórico detalhado de releituras já está reservado para uma versão futura.
- Desenho final dos endpoints e schemas de requisição/resposta.
- Como tratar versões/edições do mesmo título e usuários múltiplos.

## Critérios de desenvolvimento
Construção incremental; estudante implementa pequenos trechos e recebe explicação, revisão e testes. Não gerar aplicação inteira de forma automática.
