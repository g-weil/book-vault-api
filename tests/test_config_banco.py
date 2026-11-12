import os
from pathlib import Path
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
            ambiente_teste["BOOK_VAULT_DB_PATH"] = str(caminho)
            for _ in range(2):
                resultado = subprocess.run(
                    [sys.executable, "-c", script, str(caminho)],
                    cwd=Path(__file__).resolve().parent.parent,
                    env=ambiente_teste, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
            self.assertTrue(caminho.is_file())
