# Executar o Book Vault na VPS com Docker

O contêiner serve a API e o frontend. O SQLite fica em um volume Docker separado
da imagem, em `/data/book_vault.db`. O servidor usa um processo Uvicorn, sem reload,
e executa como usuário sem privilégios de root.

## 1. Preparar

Na VPS Linux, instale Docker Engine e o plugin Docker Compose seguindo a documentação
da sua distribuição: https://docs.docker.com/engine/install/

Envie ou clone a versão do projeto que contém Dockerfile, compose.yaml e frontend/.
As mudanças precisam estar commitadas e enviadas ao GitHub antes de usar git clone
ou git pull para obtê-las na VPS. Não copie sua .venv nem credenciais.

Na pasta do projeto, confira a instalação e a configuração:

```bash
docker --version
docker compose version
docker compose config
```

## 2. Subir

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 book-vault
```

O primeiro início cria as tabelas e carrega o catálogo de gêneros. O volume começa
com uma biblioteca vazia; o arquivo do seu computador não é incluído na imagem.
Reiniciar ou reconstruir o contêiner preserva os dados do volume.

Confira na própria VPS:

```bash
curl -f http://127.0.0.1:8000/generos
```

O Docker verifica periodicamente esse mesmo endpoint no healthcheck. O reinício
automático é aplicado se o processo encerrar; o estado unhealthy, sozinho, não
dispara um reinício pelo Compose.

## 3. Acessar pelo computador

A porta é publicada apenas em 127.0.0.1 da VPS por padrão. A aplicação ainda não
tem autenticação: quem alcançar seus endpoints pode cadastrar, editar e excluir.
Para testar com acesso privado, mantenha um túnel SSH aberto no seu computador:

```powershell
ssh -L 8080:127.0.0.1:8000 usuario@IP_DA_VPS
```

Depois abra:

- Frontend: http://127.0.0.1:8080/
- Swagger: http://127.0.0.1:8080/docs

Como o frontend usa URLs relativas, as chamadas à API passam pelo mesmo túnel.
Não é necessário configurar CORS nem iniciar o menu de terminal para usar a web.

Para usar domínio, configure um proxy reverso com HTTPS apontando para
127.0.0.1:8000 da VPS e estabeleça controle de acesso antes de disponibilizar a
aplicação para outras pessoas. Se o proxy estiver em outro contêiner, use a rede
Docker e o endereço book-vault:8000; 127.0.0.1 nesse proxy não aponta para a aplicação.

Se a porta 8000 da VPS estiver ocupada, altere somente a porta publicada:

```bash
PORT=8001 docker compose up -d --build
```

Nesse caso, ajuste também o destino do túnel ou proxy para 8001. O contêiner
continua ouvindo em 8000 internamente.

## 4. Atualizar e parar

Depois de obter a nova versão do código:

```bash
docker compose up -d --build
```

Para parar sem apagar a biblioteca:

```bash
docker compose down
```

Não use `docker compose down -v` se quiser preservar os dados: essa opção remove
o volume. Mantenha o mesmo projeto/pasta do Compose nas atualizações; outro nome de
projeto pode criar outro volume e parecer uma biblioteca nova.

## 5. Backup consistente do SQLite

Use a API de backup do SQLite para obter uma cópia consistente mesmo com o banco
aberto. O comando cria o backup no volume, e o segundo copia para a pasta da VPS:

```bash
docker compose exec -T book-vault python -c 'import sqlite3; src=sqlite3.connect("/data/book_vault.db"); dst=sqlite3.connect("/data/backup.db"); src.backup(dst); dst.close(); src.close()'
docker compose cp book-vault:/data/backup.db ./book-vault-backup.db
```

Guarde também cópias fora da VPS. Os arquivos .db não devem ser commitados.
A importação da sua biblioteca local deve ser planejada separadamente para não
substituir por acidente dados já cadastrados na VPS.
