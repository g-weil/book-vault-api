from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Autor, Genero, Livro
from schemas import AutorConsulta, LivroCadastro, LivroCadastrado, LivroConsulta


def normalizar(texto: str) -> str:
    return " ".join(texto.split()).casefold()


def cadastrar_livro(dados: LivroCadastro, session: Session) -> LivroCadastrado:
    with session.begin():
        # No SQLite, serializa cadastros para impedir duplicados em envios simultâneos.
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")

        genero_ids = set(dados.genero_ids)
        generos = session.scalars(
            select(Genero).where(Genero.id.in_(genero_ids)).order_by(Genero.id)
        ).all()
        ids_inexistentes = genero_ids - {genero.id for genero in generos}
        if ids_inexistentes:
            raise HTTPException(
                status_code=422,
                detail={
                    "mensagem": "Escolha gêneros existentes no catálogo de GET /generos.",
                    "genero_ids_inexistentes": sorted(ids_inexistentes),
                },
            )

        # A chave normalizada elimina repetições sem alterar o nome para exibição.
        nomes_autores = {}
        for nome in dados.autores or ["Autor desconhecido"]:
            nomes_autores.setdefault(normalizar(nome), nome)

        titulo_normalizado = normalizar(dados.titulo)
        candidatos = session.scalars(
            select(Livro)
            .where(Livro.titulo_normalizado == titulo_normalizado)
            .options(selectinload(Livro.autores), selectinload(Livro.generos))
        ).all()
        for existente in candidatos:
            if {autor.nome_normalizado for autor in existente.autores} == set(nomes_autores):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "mensagem": (
                            "Este livro já está cadastrado e já possui esse mesmo status."
                            if existente.status == dados.status
                            else "Este livro já está cadastrado. Deseja alterar o status?"
                        ),
                        "livro": LivroConsulta.model_validate(existente).model_dump(mode="json"),
                    },
                )

        existentes = session.scalars(
            select(Autor).where(Autor.nome_normalizado.in_(nomes_autores))
        ).all()
        por_nome = {autor.nome_normalizado: autor for autor in existentes}
        autores = []
        for nome_normalizado, nome in nomes_autores.items():
            autor = por_nome.get(nome_normalizado)
            if autor is None:
                autor = Autor(nome=nome, nome_normalizado=nome_normalizado)
                session.add(autor)
            autores.append(autor)

        livro = Livro(
            titulo=dados.titulo,
            capa_url=dados.capa_url,
            titulo_normalizado=titulo_normalizado,
            status=dados.status,
            autores=autores,
            generos=generos,
        )
        session.add(livro)
        # Envia as inserções para obter os IDs; a transação ainda não foi confirmada.
        session.flush()
        resposta = LivroCadastrado(
            mensagem="Livro cadastrado com sucesso",
            livro=LivroConsulta.model_validate(livro),
            autores_reutilizados=[AutorConsulta.model_validate(autor) for autor in existentes],
        )

    # Sair do bloco sem erro confirma a transação; qualquer erro desfaz as inserções.
    return resposta
