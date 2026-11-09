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

## Testes do menu

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes iniciam uma API em porta temporária e usam SQLite em memória, sem alterar
a biblioteca local. Simulam as entradas do terminal e fazem requisições HTTP reais.
