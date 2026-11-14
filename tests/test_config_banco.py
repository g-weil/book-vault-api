import os
from pathlib import Path
from unittest.mock import patch
import subprocess
import sys
import tempfile
import unittest


class TestCaminhoBanco(unittest.TestCase):
    def test_caminho_configuravel_preserva_dados_entre_processos(self):
        # Dois processos simulam reinícios usando o mesmo diretório persistente.
        script = """
from pathlib import Path
import sys
from sqlalchemy import select
import database
import models
assert database.DATABASE_PATH == Path(sys.argv[1]).resolve()
database.preparar_banco()
with database.SessionLocal.begin() as session:
    autor = session.scalar(select(models.Autor).where(models.Autor.nome_normalizado == 'persistente'))
    if autor is None:
        session.add(models.Autor(nome='Persistente', nome_normalizado='persistente'))
with database.SessionLocal() as session:
    assert len(session.scalars(select(models.Autor)).all()) == 1
"""
        with tempfile.TemporaryDirectory(prefix="book-vault-test-") as diretorio:
            caminho = Path(diretorio) / "data" / "book_vault.db"
            ambiente_teste = os.environ.copy()
            ambiente_teste.pop("DATABASE_URL", None)
            ambiente_teste.pop("POSTGRES_HOST", None)
            ambiente_teste["BOOK_VAULT_DB_PATH"] = str(caminho)
            for _ in range(2):
                resultado = subprocess.run(
                    [sys.executable, "-c", script, str(caminho)],
                    cwd=Path(__file__).resolve().parent.parent,
                    env=ambiente_teste, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            self.assertTrue(caminho.is_file())

    def test_sqlite_em_memoria_habilita_chaves_estrangeiras(self):
        from database import criar_engine

        engine = criar_engine("sqlite:///:memory:")
        try:
            with engine.connect() as connection:
                self.assertEqual(connection.exec_driver_sql("PRAGMA foreign_keys").scalar(), 1)
        finally:
            engine.dispose()

    def test_url_postgresql_tem_prioridade_sem_criar_arquivo_sqlite(self):
        script = """
from pathlib import Path
import sys
import database
assert database.engine.dialect.name == 'postgresql'
assert database.engine.dialect.driver == 'psycopg'
assert not Path(sys.argv[1]).parent.exists()
database.engine.dispose()
"""
        with tempfile.TemporaryDirectory(prefix="book-vault-url-test-") as diretorio:
            caminho = Path(diretorio) / "nao_criar" / "book_vault.db"
            ambiente = os.environ.copy()
            # A criação do engine não abre conexão; este teste não requer servidor.
            ambiente["DATABASE_URL"] = "postgresql://usuario:exemplo@127.0.0.1:1/teste"
            ambiente["BOOK_VAULT_DB_PATH"] = str(caminho)
            resultado = subprocess.run(
                [sys.executable, "-c", script, str(caminho)],
                cwd=Path(__file__).resolve().parent.parent,
                env=ambiente, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    def test_config_compose_preserva_senha_com_caracteres_especiais(self):
        from database import obter_url_banco

        with patch.dict(os.environ, {
            "DATABASE_URL": "", "POSTGRES_HOST": "postgres", "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "bookvault", "POSTGRES_PASSWORD": "exemplo@#/%:senha",
            "POSTGRES_DB": "book_vault",
        }):
            url = obter_url_banco()
            self.assertEqual(url.host, "postgres")
            self.assertEqual(url.password, "exemplo@#/%:senha")
            self.assertEqual(url.drivername, "postgresql+psycopg")

    def test_url_explicita_tem_prioridade_sobre_config_compose(self):
        from database import obter_url_banco

        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:", "POSTGRES_HOST": "postgres",
        }):
            self.assertEqual(obter_url_banco(), "sqlite:///:memory:")

    def test_config_postgres_incompleta_nao_cai_no_sqlite(self):
        from database import obter_url_banco

        with patch.dict(os.environ, {
            "DATABASE_URL": "", "POSTGRES_HOST": "postgres", "POSTGRES_PASSWORD": "",
        }):
            with self.assertRaises(ValueError):
                obter_url_banco()
