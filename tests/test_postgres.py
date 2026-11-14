"""Fluxos HTTP em um banco PostgreSQL descartável criado pela própria suíte."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

import database
import main
import test_menu
from cliente_api import ErroAPI
from models import Autor
from models import Genero, Livro, StatusLeitura
import migracao


@unittest.skipUnless(
    os.environ.get("BOOK_VAULT_TEST_DATABASE_URL"),
    "Defina BOOK_VAULT_TEST_DATABASE_URL para testar PostgreSQL em banco descartável.",
)
class TestPostgreSQL(test_menu.TestMenu):
    @classmethod
    def criar_banco_teste(cls):
        # A URL permite criar um novo banco; não apagamos tabelas do banco informado.
        cls.admin = database.criar_engine(os.environ["BOOK_VAULT_TEST_DATABASE_URL"])
        if cls.admin.dialect.name != "postgresql":
            cls.admin.dispose()
            raise ValueError("Os testes PostgreSQL exigem uma URL PostgreSQL.")
        cls.nome_temporario = "book_vault_test_" + uuid4().hex
        with cls.admin.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'CREATE DATABASE "{cls.nome_temporario}"')
        cls.addClassCleanup(cls.remover_banco_teste)
        return database.criar_engine(cls.admin.url.set(database=cls.nome_temporario))

    @classmethod
    def remover_banco_teste(cls):
        # Exclusivamente o nome aleatório criado acima, nunca o banco da URL.
        if hasattr(cls, "engine"):
            cls.engine.dispose()
        try:
            with cls.admin.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.exec_driver_sql(f'DROP DATABASE "{cls.nome_temporario}"')
        finally:
            cls.admin.dispose()

    def test_inicializacao_repetida_preserva_dados_e_catalogo(self):
        livro = self.cadastrar()

        async def iniciar():
            async with main.lifespan(main.app):
                pass

        with patch.object(database, "engine", self.engine), patch.object(
            main, "SessionLocal", sessionmaker(bind=self.engine)
        ):
            for _ in range(2):
                asyncio.run(iniciar())
        self.assertEqual(len(inspect(self.engine).get_table_names()), 5)
        self.assertEqual(len(self.api.requisitar("GET", "/generos")), 18)
        self.assertEqual(self.api.requisitar("GET", "/livros")["livros"][0]["id"], livro["id"])

    def simultaneos(self, pedidos):
        barreira = threading.Barrier(len(pedidos))

        def enviar(pedido):
            barreira.wait(timeout=5)
            metodo, caminho, corpo = pedido
            try:
                self.api.requisitar(metodo, caminho, corpo)
                return 201 if metodo == "POST" else 200
            except ErroAPI as erro:
                return erro.codigo

        with ThreadPoolExecutor(max_workers=len(pedidos)) as executor:
            return sorted(executor.map(enviar, pedidos))

    def test_cadastros_simultaneos_nao_duplicam_livros_ou_autores(self):
        corpo = {
            "titulo": "Livro simultâneo", "autores": ["Autor simultâneo"],
            "genero_ids": [1], "status": "Lido",
        }
        self.assertEqual(self.simultaneos([("POST", "/livros", corpo)] * 2), [201, 409])
        self.assertEqual(len(self.api.requisitar("GET", "/livros")["livros"]), 1)
        self.assertEqual(len(self.api.requisitar("GET", "/autores")), 1)
        pedidos = [("POST", "/autores", {"nome": "Outro autor"})] * 2
        self.assertEqual(self.simultaneos(pedidos), [201, 409])

    def test_edicoes_simultaneas_rejeitam_conflito(self):
        primeiro = self.cadastrar("Primeiro")
        segundo = self.cadastrar("Segundo")
        pedidos = [
            ("PATCH", f"/livros/{livro['id']}", {
                "titulo": "Mesmo destino", "autores": ["Autor novo"],
            }) for livro in [primeiro, segundo]
        ]
        self.assertEqual(self.simultaneos(pedidos), [200, 409])
        livros = self.api.requisitar("GET", "/livros")["livros"]
        self.assertEqual(sum(livro["titulo"] == "Mesmo destino" for livro in livros), 1)
        self.assertEqual(len(self.api.requisitar("GET", "/autores")), 2)

    def test_rollback_libera_bloqueio_e_nao_grava_autor(self):
        with Session(self.engine) as session:
            with self.assertRaisesRegex(ValueError, "falha simulada"):
                with database.transacao_escrita(session):
                    session.add(Autor(nome="Não salvar", nome_normalizado="não salvar"))
                    session.flush()
                    raise ValueError("falha simulada")
        self.assertEqual(self.api.requisitar("GET", "/autores"), [])
        self.cadastrar()
        with self.engine.connect() as connection:
            self.assertEqual(connection.scalar(text("SELECT count(*) FROM livros")), 1)

    def criar_origem_sqlite(self, caminho):
        origem = database.criar_engine(f"sqlite:///{caminho.as_posix()}")
        try:
            database.Base.metadata.create_all(origem)
            with Session(origem) as session, session.begin():
                autores = [
                    Autor(id=11, nome="Autora Á", nome_normalizado="autora á"),
                    Autor(id=12, nome="Autor B", nome_normalizado="autor b"),
                ]
                session.add(Autor(id=21, nome="Sem vínculo", nome_normalizado="sem vínculo"))
                session.add(Livro(
                    id=37, titulo="Livro com dois autores", titulo_normalizado="livro com dois autores",
                    status=StatusLeitura.RELENDO, capa_url="https://example.com/capa.jpg",
                    autores=autores,
                    generos=[Genero(id=9, nome="Fantasia"), Genero(id=10, nome="Terror")],
                ))
        finally:
            origem.dispose()

    def test_migracao_preserva_ids_vinculos_backup_e_proximos_ids(self):
        database.Base.metadata.drop_all(self.engine)  # Apenas o banco descartável da suíte.
        with tempfile.TemporaryDirectory(prefix="book-vault-copy-test-") as diretorio:
            origem = Path(diretorio) / "origem.db"
            self.criar_origem_sqlite(origem)
            resultado = migracao.migrar_sqlite(origem, self.engine, Path(diretorio) / "backups")
            self.assertTrue(Path(resultado["backup"]).is_file())
            self.assertEqual(resultado["registros"], {
                "autores": 3, "generos": 2, "livros": 1,
                "livros_autores": 2, "livros_generos": 2,
            })
            with closing(sqlite3.connect(origem)) as connection:
                self.assertEqual(connection.execute("SELECT id FROM livros").fetchone()[0], 37)
            with self.engine.connect() as connection:
                migracao.conferir_registros(connection, migracao.ler_registros(Path(resultado["backup"])))
            with Session(self.engine) as session, session.begin():
                autor = Autor(nome="Próximo", nome_normalizado="próximo")
                genero = Genero(nome="Próximo gênero")
                livro = Livro(titulo="Próximo", titulo_normalizado="próximo", status=StatusLeitura.LIDO)
                session.add_all([autor, genero, livro])
                session.flush()
                self.assertEqual((autor.id, genero.id, livro.id), (22, 11, 38))

    def test_migracao_rejeita_destino_preenchido_sem_alterar_dados(self):
        with tempfile.TemporaryDirectory(prefix="book-vault-copy-test-") as diretorio:
            origem = Path(diretorio) / "origem.db"
            self.criar_origem_sqlite(origem)
            backups = Path(diretorio) / "backups"
            with self.assertRaisesRegex(ValueError, "Destino não está vazio"):
                migracao.migrar_sqlite(origem, self.engine, backups)
            self.assertEqual(len(list(backups.glob("*.db"))), 1)
            self.assertEqual(len(self.api.requisitar("GET", "/generos")), 18)
            self.assertEqual(self.api.requisitar("GET", "/livros")["livros"], [])

    def test_migracao_falha_desfaz_destino_e_bloqueia_escritas_na_origem(self):
        database.Base.metadata.drop_all(self.engine)  # Apenas o banco descartável.
        with tempfile.TemporaryDirectory(prefix="book-vault-copy-test-") as diretorio:
            origem = Path(diretorio) / "origem.db"
            self.criar_origem_sqlite(origem)

            def falhar(*args):
                with closing(sqlite3.connect(origem, timeout=0)) as writer:
                    with self.assertRaises(sqlite3.OperationalError):
                        writer.execute("INSERT INTO autores VALUES (99, 'Bloqueado', 'bloqueado')")
                raise ValueError("divergência simulada")

            with patch.object(migracao, "conferir_registros", side_effect=falhar):
                with self.assertRaisesRegex(ValueError, "divergência simulada"):
                    migracao.migrar_sqlite(origem, self.engine, Path(diretorio) / "backups")
            self.assertEqual(inspect(self.engine).get_table_names(), [])
            with closing(sqlite3.connect(origem)) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM autores").fetchone()[0], 3)
