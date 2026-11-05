from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Genero


GENEROS_FIXOS = (
    "Fantasia",
    "Ficção científica",
    "Mistério e suspense",
    "Terror",
    "Romance amoroso",
    "Ficção geral",
    "Poesia e textos breves",
    "Teatro",
    "Quadrinhos",
    "Biografias e memórias",
    "História e sociedade",
    "Filosofia e espiritualidade",
    "Ciência e tecnologia",
    "Desenvolvimento pessoal e saúde",
    "Educação e estudos",
    "Negócios e economia",
    "Artes e cultura",
    "Interesses e vida prática",
)


def carregar_generos(session: Session) -> None:
    nomes_existentes = set(session.scalars(select(Genero.nome)))
    for nome in GENEROS_FIXOS:
        if nome not in nomes_existentes:
            session.add(Genero(nome=nome))
