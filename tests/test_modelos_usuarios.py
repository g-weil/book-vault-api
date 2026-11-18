"""Verifica a estrutura inicial sem alterar o banco da biblioteca real."""
import unittest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, criar_engine
from models import BibliotecaUsuario, Livro, PapelUsuario, StatusLeitura, Usuario


class TestModelosUsuarios(unittest.TestCase):
    def setUp(self):
        self.engine = criar_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session, session.begin():
            session.add_all([
                Usuario(id=1, nome="Pessoa A", email="a@example.com", email_normalizado="a@example.com"),
                Usuario(id=2, nome="Pessoa B", email="b@example.com", email_normalizado="b@example.com"),
                Livro(id=1, titulo="Livro compartilhado", titulo_normalizado="livro compartilhado", status=StatusLeitura.LENDO),
            ])

    def tearDown(self):
        self.engine.dispose()

    def test_status_independentes_e_remocao_preserva_catalogo(self):
        with Session(self.engine) as session, session.begin():
            session.add_all([
                BibliotecaUsuario(usuario_id=1, livro_id=1, status=StatusLeitura.LIDO),
                BibliotecaUsuario(usuario_id=2, livro_id=1, status=StatusLeitura.QUERO_LER),
            ])
        with Session(self.engine) as session, session.begin():
            primeiro = session.scalar(select(BibliotecaUsuario).where(BibliotecaUsuario.usuario_id == 1))
            session.delete(primeiro)
        with Session(self.engine) as session:
            self.assertIsNotNone(session.get(Livro, 1))
            restante = session.scalar(select(BibliotecaUsuario))
            self.assertEqual(restante.usuario_id, 2)
            self.assertEqual(restante.status, StatusLeitura.QUERO_LER)

    def test_nao_repete_livro_na_mesma_biblioteca(self):
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session, session.begin():
                session.add_all([
                    BibliotecaUsuario(usuario_id=1, livro_id=1, status=StatusLeitura.LIDO),
                    BibliotecaUsuario(usuario_id=1, livro_id=1, status=StatusLeitura.RELENDO),
                ])

    def test_usuario_novo_sem_privilegios_e_email_normalizado_unico(self):
        with Session(self.engine) as session:
            pessoa = session.get(Usuario, 1)
            self.assertEqual(pessoa.papel, PapelUsuario.USUARIO)
            self.assertFalse(pessoa.ativo)
            self.assertIsNone(pessoa.senha_hash)
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session, session.begin():
                session.add(Usuario(nome="Duplicado", email="A@example.com", email_normalizado="a@example.com"))

    def test_vinculo_exige_usuario_e_livro_existentes(self):
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session, session.begin():
                session.add(BibliotecaUsuario(usuario_id=999, livro_id=1, status=StatusLeitura.LIDO))

    def test_nao_ativa_conta_sem_hash(self):
        with self.assertRaises(IntegrityError):
            with Session(self.engine) as session, session.begin():
                session.get(Usuario, 1).ativo = True

    def test_personalizacoes_nao_alteram_catalogo_ou_outra_biblioteca(self):
        with Session(self.engine) as session, session.begin():
            session.add_all([
                BibliotecaUsuario(usuario_id=1, livro_id=1, status=StatusLeitura.LIDO,
                                  personalizacoes={"titulo": "Meu título", "capa_url": None}),
                BibliotecaUsuario(usuario_id=2, livro_id=1, status=StatusLeitura.LENDO),
            ])
        with Session(self.engine) as session:
            self.assertEqual(session.get(Livro, 1).titulo, "Livro compartilhado")
            entradas = session.scalars(select(BibliotecaUsuario).order_by(BibliotecaUsuario.usuario_id)).all()
            self.assertEqual(entradas[0].personalizacoes["titulo"], "Meu título")
            self.assertIn("capa_url", entradas[0].personalizacoes)
            self.assertIsNone(entradas[0].personalizacoes["capa_url"])
            self.assertEqual(entradas[1].personalizacoes, {})
