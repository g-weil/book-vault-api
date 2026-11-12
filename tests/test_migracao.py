import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, inspect

import database
import models  # Registra os modelos antes de preparar o banco de teste.


class TestMigracaoCapa(unittest.TestCase):
    def test_banco_antigo_preserva_livro_e_pode_iniciar_duas_vezes(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    "CREATE TABLE livros (id INTEGER PRIMARY KEY, titulo VARCHAR NOT NULL, "
                    "titulo_normalizado VARCHAR NOT NULL, status VARCHAR NOT NULL)"
                )
                connection.exec_driver_sql(
                    "INSERT INTO livros VALUES (7, 'O Hobbit', 'o hobbit', 'Lido')"
                )
            with patch.object(database, "engine", engine):
                database.preparar_banco()
                database.preparar_banco()
            with engine.connect() as connection:
                livro = connection.exec_driver_sql("SELECT * FROM livros").one()
                self.assertEqual(tuple(livro), (7, "O Hobbit", "o hobbit", "Lido", None))
            self.assertIn("capa_url", {c["name"] for c in inspect(engine).get_columns("livros")})
        finally:
            engine.dispose()
