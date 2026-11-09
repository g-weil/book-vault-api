from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from cadastro import normalizar
from models import Autor, Livro
from schemas import AutorCadastro, AutorConsulta, AutorEdicao


def cadastrar_autor(dados: AutorCadastro, session: Session) -> AutorConsulta:
    with session.begin():
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        nome_normalizado = normalizar(dados.nome)
        existente = session.scalar(select(Autor).where(Autor.nome_normalizado == nome_normalizado))
        if existente is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "mensagem": "Este autor já está cadastrado.",
                    "autor": AutorConsulta.model_validate(existente).model_dump(),
                },
            )
        autor = Autor(nome=dados.nome, nome_normalizado=nome_normalizado)
        session.add(autor)
        session.flush()
        resposta = AutorConsulta.model_validate(autor)
    return resposta


def editar_autor(autor_id: int, dados: AutorEdicao, session: Session) -> AutorConsulta:
    with session.begin():
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        autor = session.get(Autor, autor_id)
        if autor is None:
            raise HTTPException(status_code=404, detail="Autor não encontrado.")
        nome_normalizado = normalizar(dados.nome)
        existente = session.scalar(
            select(Autor).where(Autor.nome_normalizado == nome_normalizado, Autor.id != autor_id)
        )
        if existente is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "mensagem": "O nome informado já pertence a outro autor cadastrado.",
                    "autor": AutorConsulta.model_validate(existente).model_dump(),
                },
            )
        # Os livros continuam apontando para o mesmo ID, agora com o nome corrigido.
        autor.nome = dados.nome
        autor.nome_normalizado = nome_normalizado
        session.flush()
        resposta = AutorConsulta.model_validate(autor)
    return resposta


def excluir_autor(autor_id: int, session: Session) -> None:
    with session.begin():
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        autor = session.get(Autor, autor_id)
        if autor is None:
            raise HTTPException(status_code=404, detail="Autor não encontrado.")
        livro_vinculado = session.scalar(
            select(Livro.id).where(Livro.autores.any(Autor.id == autor_id)).limit(1)
        )
        if livro_vinculado is not None:
            raise HTTPException(
                status_code=409,
                detail="Não é possível excluir um autor com livros vinculados.",
            )
        session.delete(autor)
