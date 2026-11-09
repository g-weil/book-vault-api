from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

import models  # Registra as tabelas em Base.metadata antes de criá-las.
from catalogo import carregar_generos
from cadastro import cadastrar_livro, normalizar
from autores import cadastrar_autor, editar_autor, excluir_autor
from database import Base, SessionLocal, engine, obter_sessao
from edicao import editar_livro
from schemas import (
    AutorCadastro,
    AutorEdicao,
    AutorConsulta,
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


@app.delete(
    "/livros/{livro_id}", status_code=204, response_class=Response, tags=["Livros"],
    responses={404: {"description": "Livro não encontrado."}},
)
def remover_livro(
    livro_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(obter_sessao)],
):
    with session.begin():
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        livro = session.get(models.Livro, livro_id)
        if livro is None:
            raise HTTPException(status_code=404, detail="Livro não encontrado.")
        # O ORM remove os vínculos associativos, preservando autores e gêneros.
        session.delete(livro)
    return Response(status_code=204)


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


@app.post(
    "/autores", response_model=AutorConsulta, status_code=201, tags=["Autores"],
    responses={409: {"description": "Autor já cadastrado."}},
)
def criar_autor(dados: AutorCadastro, session: Annotated[Session, Depends(obter_sessao)]):
    return cadastrar_autor(dados, session)


@app.patch(
    "/autores/{autor_id}", response_model=AutorConsulta, tags=["Autores"],
    responses={404: {"description": "Autor não encontrado."}, 409: {"description": "Nome já utilizado."}},
)
def atualizar_autor(
    autor_id: Annotated[int, Path(gt=0)],
    dados: AutorEdicao,
    session: Annotated[Session, Depends(obter_sessao)],
):
    return editar_autor(autor_id, dados, session)


@app.delete(
    "/autores/{autor_id}", status_code=204, response_class=Response, tags=["Autores"],
    responses={
        404: {"description": "Autor não encontrado."},
        409: {"description": "Autor possui livros vinculados."},
    },
)
def remover_autor(
    autor_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(obter_sessao)],
):
    excluir_autor(autor_id, session)
    return Response(status_code=204)


@app.get("/autores", response_model=list[AutorConsulta], tags=["Autores"])
def listar_autores(
    session: Annotated[Session, Depends(obter_sessao)],
    nome: Annotated[
        str | None,
        Query(min_length=1, description="Parte do nome do autor; omita para listar todos."),
    ] = None,
):
    consulta = select(models.Autor).order_by(models.Autor.id)
    if nome is not None:
        termo = normalizar(nome)
        if not termo:
            raise HTTPException(status_code=422, detail="Informe parte do nome ou omita o filtro.")
        consulta = consulta.where(models.Autor.nome_normalizado.contains(termo, autoescape=True))
    return session.scalars(consulta).all()


@app.get("/generos", response_model=list[GeneroConsulta], tags=["Gêneros"])
def listar_generos(session: Annotated[Session, Depends(obter_sessao)]):
    consulta = select(models.Genero).order_by(models.Genero.id)
    return session.scalars(consulta).all()


@app.get("/livros", response_model=BibliotecaConsulta, tags=["Livros"])
def listar_livros(
    session: Annotated[Session, Depends(obter_sessao)],
    autor_id: Annotated[int | None, Query(gt=0, description="ID do autor; use apenas um filtro.")] = None,
    autor_nome: Annotated[
        str | None, Query(min_length=1, description="Parte do nome do autor; use apenas um filtro.")
    ] = None,
):
    if autor_id is not None and autor_nome is not None:
        raise HTTPException(status_code=422, detail="Escolha apenas um filtro: autor_id ou autor_nome.")

    consulta = (
        select(models.Livro)
        .options(
            selectinload(models.Livro.autores),
            selectinload(models.Livro.generos),
        )
        .order_by(models.Livro.id)
    )
    if autor_id is not None:
        consulta = consulta.where(models.Livro.autores.any(models.Autor.id == autor_id))
    elif autor_nome is not None:
        termo = normalizar(autor_nome)
        if not termo:
            raise HTTPException(status_code=422, detail="Informe parte do nome ou omita o filtro.")
        consulta = consulta.where(
            models.Livro.autores.any(models.Autor.nome_normalizado.contains(termo, autoescape=True))
        )

    livros = session.scalars(consulta).all()
    if livros:
        mensagem = "Biblioteca consultada com sucesso"
    elif autor_id is not None or autor_nome is not None:
        mensagem = "Nenhum livro encontrado para esse autor"
    else:
        mensagem = "Sua biblioteca está vazia"
    return {
        "mensagem": mensagem,
        "livros": livros,
    }
