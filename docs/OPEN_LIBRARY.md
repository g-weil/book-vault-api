# Open Library — revisão e plano de integração

Revisão em 16/11/2026. A integração e o catálogo multiusuário ainda não foram
implementados. Este documento compara as regras publicadas com o uso planejado;
não representa uma autorização individual concedida pela Open Library.

## Conclusão

Pesquisa bibliográfica pontual, iniciada pelo usuário, é compatível em princípio
com os casos de descoberta descritos pela Open Library. Essa conclusão depende
do comportamento real e do volume de acesso. Não interpretar como permissão para
replicar o catálogo, automatizar coleta ou usar a API como infraestrutura de um
serviço comercial de alto tráfego.

## Acesso à API

As [diretrizes oficiais](https://openlibrary.org/developers/api) pedem identificação
da aplicação com User-Agent e contato, recomendam cache e proíbem coleta em massa,
scraping e distribuição de requisições por IPs para contornar limites. Os limites
publicados são 1 requisição/s sem identificação e 3/s com identificação.

No Book Vault, controlar o total de solicitações externas, não conceder esse limite
a cada usuário. Começar conservadoramente, com fila, cache e pausa na digitação;
debounce sozinho não controla a soma dos acessos. Tratar timeout, 429, 403 e falhas
sem insistência contínua. Respeitar Retry-After quando informado. Não pré-carregar
todas as páginas nem buscar detalhes individuais de todos os resultados.

A página solicita registro da aplicação por formulário. Definir e-mail de contato
e registrar o uso antes da publicação; isso ainda não foi feito. Não foi enviada
mensagem nem formulário em nome do usuário durante esta revisão.

## Busca e identidade dos registros

A [Search API](https://openlibrary.org/dev/docs/api/search) permite pesquisa e
paginação com campos selecionados. Evitar `fields=*`. A resposta padrão representa
obras, não necessariamente uma edição específica. Separar obra e edição quando
for necessário identificar idioma, ISBN ou capa; guardar fonte e identificadores
externos, sem deduplicar autores apenas pelo nome. O schema externo pode mudar:
validar os campos e aceitar dados ausentes, sem inventar metadados.

## Armazenamento e direitos

O [licenciamento](https://openlibrary.org/developers/licensing) informa que o
Internet Archive não reivindica novos direitos sobre a base, mas ressalva direitos
existentes em contribuições e jurisdições. Isso não equivale a uma declaração de
domínio público para todo conteúdo nem a uma licença irrestrita para textos e imagens.

O plano é manter cache de pesquisas e persistir somente os metadados necessários
dos registros escolhidos, com fonte, identificador e data de obtenção. Cache
temporário e persistência de uma entrada na biblioteca são finalidades distintas.
A recomendação de cache não é, sozinha, autorização explícita para qualquer catálogo
permanente redistribuído. Se o uso evoluir para espelho, distribuição em massa ou
serviço comercial de alto tráfego, reavaliar e consultar a Open Library.
Não importar textos integrais ou descrições extensas automaticamente.

Os termos gerais do Internet Archive, acessados pelo rodapé, não retornaram texto
legível na ferramenta desta revisão. Precisam de leitura no navegador antes da
publicação: [termos gerais](https://archive.org/about/terms). A revisão não pode
ser apresentada como confirmação jurídica integral de todos os termos.

## Capas

A [Covers API](https://openlibrary.org/dev/docs/api/covers) orienta exibição pública
com imagens carregadas diretamente de `covers.openlibrary.org`, sem varredura ou
download em massa. Preferir CoverID ou OLID quando disponíveis. Há limite publicado
de 100 acessos por IP em cinco minutos para outros identificadores. Ausência de
capa deve usar nosso placeholder. Não assumir que armazenar a URL transfere
direitos de reprodução da imagem. Acrescentar link para a fonte como cortesia;
a documentação agradece esse crédito, sem apresentá-lo como condição geral obrigatória.

## Regras de produto aprovadas

- Catálogo bibliográfico compartilhado, com bibliotecas pessoais privadas.
- Status e avaliação pertencem à entrada do usuário na biblioteca.
- Busca local e consulta externa sob demanda; não baixar dumps nesta etapa.
- Cadastro manual para livros não encontrados. A decisão mais recente prioriza
  catálogo local compartilhado com sugestões de cadastros e bibliotecas privadas;
  substitui a proposta de registros particulares. Fechar permissões de curadoria
  antes de implementar. A integração externa está em espera enquanto fazemos usuários.
- Confirmar pelo menos um gênero do nosso catálogo ao adicionar um livro externo.
  Incluir `Outros`, mantendo a escolha explícita; não criar gêneros automaticamente.
- Um usuário comum não pode alterar metadados compartilhados e afetar outras contas.
- Essas decisões exigem nova modelagem e migração com preservação dos livros atuais.
  Ainda definir obra/edição, vínculos de gêneros pessoais e permissões administrativas.

## Antes de implementar

Fechar a modelagem de catálogo e biblioteca, depois usuários/isolamento, cliente
externo com cache/limites e a interface de seleção. Testar as falhas do fornecedor
com respostas simuladas; não usar a API pública como dependência da suíte de CI.
Verificar fonte/contato, termos gerais e plano de publicação. O sistema atual ainda
não oferece autenticação ou bibliotecas privadas.
