from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

import models  # Registra as tabelas em Base.metadata antes de criá-las.
from catalogo import carregar_generos
from cadastro import cadastrar_livro
from database import Base, SessionLocal, engine, obter_sessao
from schemas import BibliotecaConsulta, GeneroConsulta, LivroCadastro, LivroCadastrado


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal.begin() as session:
        carregar_generos(session)
    yield


app = FastAPI(title="Book Vault API", lifespan=lifespan)


@app.post(
    "/livros",
    response_model=LivroCadastrado,
    status_code=201,
    tags=["Livros"],
    responses={
        409: {"description": "Livro já cadastrado; retorna os dados existentes sem alterar o status."},
        422: {"description": "Dados inválidos ou IDs de gêneros inexistentes."},
    },
)
def criar_livro(dados: LivroCadastro, session: Annotated[Session, Depends(obter_sessao)]):
    return cadastrar_livro(dados, session)


@app.get("/generos", response_model=list[GeneroConsulta], tags=["Gêneros"])
def listar_generos(session: Annotated[Session, Depends(obter_sessao)]):
    consulta = select(models.Genero).order_by(models.Genero.id)
    return session.scalars(consulta).all()


@app.get("/livros", response_model=BibliotecaConsulta, tags=["Livros"])
def listar_livros(session: Annotated[Session, Depends(obter_sessao)]):
    consulta = (
        select(models.Livro)
        .options(
            selectinload(models.Livro.autores),
            selectinload(models.Livro.generos),
        )
        .order_by(models.Livro.id)
    )
    livros = session.scalars(consulta).all()
    return {
        "mensagem": "Biblioteca consultada com sucesso" if livros else "Sua biblioteca está vazia",
        "livros": livros,
    }
