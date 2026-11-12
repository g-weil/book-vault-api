import io
import socket
import threading
import time
import unittest
import shutil
import subprocess
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.request import urlopen

import uvicorn
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import menu
from catalogo import carregar_generos
from cliente_api import ClienteAPI, ErroAPI
from database import Base, obter_sessao
from main import app


class TestMenu(unittest.TestCase):
    """Exercita entradas do terminal com HTTP real e banco isolado em memória."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def ativar_chaves(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        def sessao_teste():
            with Session(cls.engine) as session:
                yield session

        app.dependency_overrides[obter_sessao] = sessao_teste
        cls.socket = socket.socket()
        cls.socket.bind(("127.0.0.1", 0))
        cls.api = ClienteAPI(f"http://127.0.0.1:{cls.socket.getsockname()[1]}")
        # Desliga apenas o lifespan desta instância para não abrir o banco local.
        cls.server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_level="critical"))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={"sockets": [cls.socket]}, daemon=True)
        cls.thread.start()
        for _ in range(100):
            if cls.server.started:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("Servidor de teste não iniciou.")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=5)
        cls.socket.close()
        app.dependency_overrides.pop(obter_sessao, None)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session, session.begin():
            carregar_generos(session)

    def interagir(self, funcao, entradas):
        saida = io.StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            funcao(self.api)
        return saida.getvalue()

    def cadastrar(self, titulo="O Hobbit", autores=None):
        return self.api.requisitar("POST", "/livros", {
            "titulo": titulo, "autores": autores or ["Tolkien"],
            "genero_ids": [1], "status": "Quero ler",
        })["livro"]

    def test_cadastro_validacao_e_autor_desconhecido(self):
        saida = self.interagir(menu.cadastrar_livro, ["  O Hobbit ", "", "999", "1,2", "9", "2"])
        self.assertIn("Gêneros disponíveis", saida)
        livro = self.api.requisitar("GET", "/livros")["livros"][0]
        self.assertEqual(livro["autores"][0]["nome"], "Autor desconhecido")
        self.assertEqual(livro["status"], "Lendo")
        self.assertEqual(len(livro["generos"]), 2)

    def test_duplicidade_pergunta_antes_de_alterar(self):
        self.cadastrar()
        self.interagir(menu.cadastrar_livro, ["O Hobbit", "Tolkien", "1", "3", "n"])
        self.assertEqual(self.api.requisitar("GET", "/livros")["livros"][0]["status"], "Quero ler")
        self.interagir(menu.cadastrar_livro, ["O Hobbit", "Tolkien", "1", "3", "s", "4"])
        self.assertEqual(self.api.requisitar("GET", "/livros")["livros"][0]["status"], "Relendo")

    def test_duplicidade_com_mesmo_status_nao_oferece_alteracao(self):
        self.cadastrar()
        saida = self.interagir(menu.cadastrar_livro, ["O Hobbit", "Tolkien", "1", "1"])
        self.assertIn("já possui esse mesmo status", saida)
        with self.assertRaises(ErroAPI) as erro:
            self.cadastrar()
        self.assertEqual(erro.exception.codigo, 409)
        self.assertIn("já possui esse mesmo status", str(erro.exception))
        livros = self.api.requisitar("GET", "/livros")["livros"]
        self.assertEqual(len(livros), 1)
        self.assertEqual(livros[0]["status"], "Quero ler")

    def test_busca_nome_parcial_e_selecao_por_id(self):
        livro = self.cadastrar(autores=["José Saramago"])
        self.cadastrar("Outro livro", ["Outro autor"])
        id_autor = str(livro["autores"][0]["id"])
        saida = self.interagir(menu.buscar_por_autor, ["JOSÉ", id_autor])
        self.assertIn("O Hobbit", saida)
        self.assertNotIn("Outro livro", saida)

    def test_edicao_preserva_brancos_e_substitui_generos(self):
        livro = self.cadastrar()
        self.interagir(menu.editar_livro, [str(livro["id"]), "Novo título", "", "2", "s"])
        atual = self.api.requisitar("GET", "/livros")["livros"][0]
        self.assertEqual(atual["titulo"], "Novo título")
        self.assertEqual(atual["autores"], livro["autores"])
        self.assertEqual([g["id"] for g in atual["generos"]], [2])
        self.assertEqual(atual["status"], livro["status"])

    def test_cancelar_e_confirmar_exclusao(self):
        livro = self.cadastrar()
        self.interagir(menu.excluir_livro, [str(livro["id"]), "n"])
        self.assertEqual(len(self.api.requisitar("GET", "/livros")["livros"]), 1)
        self.interagir(menu.excluir_livro, [str(livro["id"]), "s"])
        self.assertEqual(self.api.requisitar("GET", "/livros")["livros"], [])
        self.assertEqual(len(self.api.requisitar("GET", "/autores")), 1)

    def test_gerenciamento_autores_e_recusa_de_exclusao(self):
        self.interagir(menu.gerenciar_autores, ["2", "Autor novo", "3", "novo", "1", "Nome corrigido", "s", "0"])
        self.assertEqual(self.api.requisitar("GET", "/autores")[0]["nome"], "Nome corrigido")
        self.cadastrar(autores=["Nome corrigido"])
        saida = self.interagir(menu.gerenciar_autores, ["4", "", "1", "s", "0"])
        self.assertIn("livros vinculados", saida)
        self.assertEqual(len(self.api.requisitar("GET", "/autores")), 1)

    def test_erros_api_e_conexao(self):
        self.api.requisitar("POST", "/autores", {"nome": "Autor"})
        with self.assertRaises(ErroAPI) as erro:
            self.api.requisitar("POST", "/autores", {"nome": "autor"})
        self.assertEqual(erro.exception.codigo, 409)
        with socket.socket() as sem_servidor:
            sem_servidor.bind(("127.0.0.1", 0))
            cliente = ClienteAPI(f"http://127.0.0.1:{sem_servidor.getsockname()[1]}")
            with self.assertRaises(ConnectionError):
                cliente.requisitar("GET", "/livros")

    def test_menu_opcao_invalida_e_saida(self):
        saida = self.interagir(menu.executar, ["9", "2", "0"])
        self.assertIn("Opção inválida", saida)
        self.assertIn("Sua biblioteca está vazia", saida)
        self.assertIn("Até a próxima", saida)

    def test_busca_titulo_parcial_e_combinacao_com_autor(self):
        primeiro = self.cadastrar("Saga Volume 1", ["Autor A"])
        self.cadastrar("Saga Volume 2", ["Autor A"])
        self.cadastrar("Saga Volume 1", ["Autor B"])
        self.cadastrar("100% Outro", ["Autor B"])
        resultado = self.api.requisitar("GET", "/livros", parametros={"titulo": "  SAGA   VOLUME "})
        self.assertEqual(len(resultado["livros"]), 3)
        resultado = self.api.requisitar("GET", "/livros", parametros={
            "titulo": "saga", "autor_id": primeiro["autores"][0]["id"],
        })
        self.assertEqual(len(resultado["livros"]), 2)
        resultado = self.api.requisitar("GET", "/livros", parametros={"titulo": "%"})
        self.assertEqual([livro["titulo"] for livro in resultado["livros"]], ["100% Outro"])
        resultado = self.api.requisitar("GET", "/livros", parametros={"titulo": "inexistente"})
        self.assertEqual(resultado["livros"], [])
        for titulo in ("", "   "):
            with self.assertRaises(ErroAPI) as erro:
                self.api.requisitar("GET", "/livros", parametros={"titulo": titulo})
            self.assertEqual(erro.exception.codigo, 422)

    def test_capa_opcional_validacao_edicao_e_remocao(self):
        livro = self.cadastrar()
        self.assertIsNone(livro["capa_url"])
        caminho = f"/livros/{livro['id']}"
        capa = "https://example.com/capa.jpg"
        atualizado = self.api.requisitar("PATCH", caminho, {"capa_url": capa})
        self.assertEqual(atualizado["capa_url"], capa)
        atualizado = self.api.requisitar("PATCH", caminho, {"titulo": "Título corrigido"})
        self.assertEqual(atualizado["capa_url"], capa)
        for invalida in ("javascript:alert(1)", "file:///capa.jpg", "não é uma URL", 123):
            with self.assertRaises(ErroAPI) as erro:
                self.api.requisitar("PATCH", caminho, {"capa_url": invalida})
            self.assertEqual(erro.exception.codigo, 422)
        for vazia in ("", None):
            atualizado = self.api.requisitar("PATCH", caminho, {"capa_url": vazia})
            self.assertIsNone(atualizado["capa_url"])
        resposta = self.api.requisitar("POST", "/livros", {
            "titulo": "Livro com capa", "autores": [], "genero_ids": [1],
            "status": "Lendo", "capa_url": capa,
        })
        self.assertEqual(resposta["livro"]["capa_url"], capa)

    def test_pagina_e_arquivos_estaticos(self):
        for caminho, tipo in (("/", "text/html"), ("/static/styles.css", "text/css"),
                              ("/static/app.js", "javascript"), ("/static/livro.svg", "image/svg+xml")):
            with urlopen(self.api.endereco + caminho) as resposta:
                self.assertEqual(resposta.status, 200)
                self.assertIn(tipo, resposta.headers["Content-Type"])
                self.assertEqual(resposta.headers["Cache-Control"], "no-cache")
                self.assertTrue(resposta.read())

    @unittest.skipUnless(shutil.which("node"), "Node.js não instalado; necessário apenas para este teste de JavaScript.")
    def test_cadastro_frontend_eventos_e_http_real(self):
        resultado = subprocess.run(
            [shutil.which("node"), "tests/frontend_cadastro.cjs", self.api.endereco],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()
