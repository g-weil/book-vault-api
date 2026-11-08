from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from cadastro import normalizar
from models import Autor, Genero, Livro
from schemas import LivroConsulta, LivroEdicao


def editar_livro(livro_id: int, dados: LivroEdicao, session: Session) -> LivroConsulta:
    with session.begin():
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        livro = session.get(Livro, livro_id)
        if livro is None:
            raise HTTPException(status_code=404, detail="Livro não encontrado.")

        campos = dados.model_fields_set
        titulo = dados.titulo if "titulo" in campos else livro.titulo
        titulo_normalizado = normalizar(titulo)

        # Na edição, autores em branco preservam os vínculos atuais.
        nomes = None
        if dados.autores:
            nomes = {}
            for nome in dados.autores:
                nomes.setdefault(normalizar(nome), nome)
        nomes_finais = set(nomes) if nomes else {a.nome_normalizado for a in livro.autores}

        generos = None
        if "genero_ids" in campos:
            ids = set(dados.genero_ids)
            generos = session.scalars(
                select(Genero).where(Genero.id.in_(ids)).order_by(Genero.id)
            ).all()
            inexistentes = ids - {g.id for g in generos}
            if inexistentes:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "mensagem": "Escolha gêneros existentes no catálogo de GET /generos.",
                        "genero_ids_inexistentes": sorted(inexistentes),
                    },
                )

        candidatos = session.scalars(
            select(Livro)
            .where(Livro.id != livro_id, Livro.titulo_normalizado == titulo_normalizado)
            .options(selectinload(Livro.autores), selectinload(Livro.generos))
        ).all()
        for existente in candidatos:
            if {a.nome_normalizado for a in existente.autores} == nomes_finais:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "mensagem": "A alteração resultaria em um livro já cadastrado.",
                        "livro": LivroConsulta.model_validate(existente).model_dump(mode="json"),
                    },
                )

        if nomes:
            existentes = session.scalars(
                select(Autor).where(Autor.nome_normalizado.in_(nomes))
            ).all()
            por_nome = {a.nome_normalizado: a for a in existentes}
            autores = []
            for chave, nome in nomes.items():
                autor = por_nome.get(chave)
                if autor is None:
                    autor = Autor(nome=nome, nome_normalizado=chave)
                    session.add(autor)
                autores.append(autor)
            livro.autores = autores

        livro.titulo = titulo
        livro.titulo_normalizado = titulo_normalizado
        if generos is not None:
            livro.generos = generos
        session.flush()
        resposta = LivroConsulta.model_validate(livro)
    return resposta
