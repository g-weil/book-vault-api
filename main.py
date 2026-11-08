from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

import models  # Registra as tabelas em Base.metadata antes de criá-las.
from catalogo import carregar_generos
from cadastro import cadastrar_livro
from database import Base, SessionLocal, engine, obter_sessao
from edicao import editar_livro
from schemas import (
    BibliotecaConsulta,
    GeneroConsulta,
    LivroCadastro,
    LivroCadastrado,
    LivroConsulta,
    LivroStatusAlteracao,
    LivroEdicao,
)


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


@app.patch(
    "/livros/{livro_id}",
    response_model=LivroConsulta,
    tags=["Livros"],
    responses={
        404: {"description": "Livro não encontrado."},
        409: {"description": "A edição resultaria em um livro duplicado."},
        422: {"description": "Dados inválidos ou gêneros inexistentes."},
    },
)
def atualizar_livro(
    livro_id: Annotated[int, Path(gt=0)],
    dados: LivroEdicao,
    session: Annotated[Session, Depends(obter_sessao)],
):
    return editar_livro(livro_id, dados, session)


@app.patch(
    "/livros/{livro_id}/status",
    response_model=LivroConsulta,
    tags=["Livros"],
    responses={404: {"description": "Livro não encontrado."}},
)
def alterar_status(
    livro_id: Annotated[int, Path(gt=0)],
    dados: LivroStatusAlteracao,
    session: Annotated[Session, Depends(obter_sessao)],
):
    with session.begin():
        livro = session.get(models.Livro, livro_id)
        if livro is None:
            raise HTTPException(status_code=404, detail="Livro não encontrado.")
        livro.status = dados.status
        resposta = LivroConsulta.model_validate(livro)
    return resposta


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
