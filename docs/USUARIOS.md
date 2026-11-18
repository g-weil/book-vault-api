# Usuários e bibliotecas pessoais — implementação incremental

## Etapa atual: modelos preparados

`Usuario` contém identificação, e-mail normalizado único, hash de senha opcional
enquanto a conta não estiver ativada, indicador de conta ativa, papel e data.
O papel padrão é `usuario`; privilégios administrativos nunca serão escolhidos
pelo formulário público. Uma restrição impede ativar a conta sem um hash.

`BibliotecaUsuario` relaciona uma conta a um livro do catálogo. Guarda seu próprio
status, data de adição e personalizações. A restrição única de usuário/livro impede
adicionar o mesmo registro duas vezes à mesma biblioteca. Duas contas podem ter
o mesmo livro com estados e personalizações diferentes.

`personalizacoes` guarda somente diferenças locais, em JSON. As chaves serão
limitadas e validadas pelos schemas dos próximos endpoints: título, autores,
gêneros e capa. Uma chave ausente herda o catálogo; capa explicitamente nula
remove a imagem apenas daquela entrada. O usuário não editará esse JSON diretamente.
A alteração local não cria uma nova identidade no catálogo nem afeta sugestões
para outras contas. Atualizações futuras substituirão o dicionário validado,
evitando depender da detecção automática de alterações aninhadas do ORM.

Remover um `BibliotecaUsuario` preserva o livro do catálogo e os vínculos de
outros usuários. Correções globais e exclusão de registros compartilhados ficam
restritas à administração; permissões administrativas detalhadas ainda serão fechadas.

## Compatibilidade durante a transição

O campo `Livro.status` foi mantido como legado para não quebrar as rotas atuais.
Ele não deve ser utilizado para usuários diferentes: depois da adaptação,
as operações usarão `BibliotecaUsuario.status`. A sincronização e o corte definitivo
serão feitos com backup e testes, não por uma alteração destrutiva agora.

Os modelos foram testados com bancos isolados. A nova estrutura não foi aplicada
à biblioteca real nesta etapa; a conta administrativa também não foi criada ou
ativada. Os dados da primeira conta serão fornecidos localmente, sem senha em chat
e sem informações pessoais no código versionado.

O importador `migracao.py` permanece específico às cinco tabelas do legado SQLite.
Não pode ser usado para transportar contas e bibliotecas multiusuário. A leitura
rejeita fontes com dados nessas novas tabelas em vez de descartá-los silenciosamente.

**Ainda não existem login, sessão ou isolamento nos endpoints em execução.**
Criar tabelas não implementa controle de acesso. Não considerar esta etapa pronta
para hospedagem pública de bibliotecas privadas.

## Próximas etapas

1. Preparar a migração aditiva e a criação controlada da primeira conta, preservando
   IDs, dados e estados atuais; definir senha localmente com hash seguro.
2. Implementar autenticação, sessão com expiração, identificação da conta e logout.
3. Adaptar cada operação para consultar o vínculo do usuário, aplicar suas
   personalizações e impedir acesso direto às entradas alheias.
4. Criar consultas do catálogo e a adição de livros existentes à biblioteca,
   preservando as informações pessoais na resposta e os metadados globais intactos.
5. Integrar cadastro/login no frontend e autenticação no menu/Swagger; testar duas
   contas, permissões, erros, remoção pessoal e mudanças particulares.

Na criação de uma conta nova, ainda confirmar se o cadastro será livre ou por convite.
Open Library e avaliações continuam em espera. Quando as avaliações forem retomadas,
o campo pertencerá ao vínculo da biblioteca, não ao livro compartilhado.
