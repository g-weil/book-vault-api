# Book Vault API

Biblioteca pessoal com livros, autores, gêneros e cinco status de leitura.

## Executar

Na pasta do projeto, instale as dependências no ambiente virtual:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicie a API no primeiro terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

Frontend web (primeira etapa): http://127.0.0.1:8000/

A página usa HTML, CSS e JavaScript puro e o mesmo servidor da API; não é preciso
instalar Node.js nem iniciar um segundo servidor para a interface web. Nesta etapa,
exibe livros em cards e permite cadastrar, editar título/autores/gêneros/capa,
atualizar o status e excluir com confirmação em modais. A barra lateral também
abre a área Autores, com listagem de nomes/IDs, busca parcial, cadastro, edição e
exclusão com confirmação. Autores com livros vinculados têm a exclusão bloqueada.
A biblioteca permite buscar por título enquanto digita, selecionar volumes nas
sugestões e combinar título, autor e status. Os filtros podem ser limpos separadamente.
O restante dos
formulários será integrado progressivamente.

O campo de capa aceita endereço HTTP/HTTPS de imagem e é opcional. Se estiver vazio
ou a imagem falhar, aparece uma capa padrão. O banco guarda o link, não a imagem.
Livros já cadastrados são preservados ao adicionar essa coluna na inicialização.

Em um segundo terminal, na mesma pasta, inicie o menu:

```powershell
.\.venv\Scripts\python.exe menu.py
```

O menu usa a API e precisa que o primeiro terminal continue executando o servidor.
Livros e autores cadastrados pelo menu são gravados no mesmo SQLite da API.

No cadastro, separe autores por ponto e vírgula e IDs de gêneros por vírgula.
As opções de gêneros e status são exibidas antes da escolha. Use `0` para voltar
nas seleções ou sair do menu principal. Exclusões são definitivas e exigem confirmação.

As regras de negócio estão em REQUISITOS.md. O banco local e o ambiente virtual
não são versionados; as tabelas e o catálogo são criados na inicialização da API.

## Docker e VPS

Com Docker e Compose instalados, execute `docker compose up -d --build`.
A API e o frontend ficam no mesmo contêiner; os dados SQLite persistem em volume.
Por padrão a porta fica restrita ao acesso local da máquina hospedeira.

Veja [o guia da VPS](docs/DEPLOY_VPS.md) para acesso por SSH, atualizações e backups.
O banco local não é enviado automaticamente para o contêiner.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes iniciam uma API em porta temporária e usam SQLite em memória, sem alterar
a biblioteca local. Simulam as entradas do terminal e fazem requisições HTTP reais.

Se Node.js estiver disponível, a suíte também verifica os eventos do cadastro web
com um DOM simplificado e HTTP real para a API temporária. Esse teste não substitui
a revisão visual e de interação em um navegador. Node.js não é necessário para usar o frontend.
