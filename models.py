from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class StatusLeitura(str, Enum):
    QUERO_LER = "Quero ler"
    LENDO = "Lendo"
    LIDO = "Lido"
    RELENDO = "Relendo"
    ABANDONADO = "Abandonado"


# A chave primária composta impede repetir o mesmo vínculo.
livros_autores = Table(
    "livros_autores",
    Base.metadata,
    Column("livro_id", ForeignKey("livros.id"), primary_key=True),
    Column("autor_id", ForeignKey("autores.id"), primary_key=True),
)

livros_generos = Table(
    "livros_generos",
    Base.metadata,
    Column("livro_id", ForeignKey("livros.id"), primary_key=True),
    Column("genero_id", ForeignKey("generos.id"), primary_key=True),
)


class Autor(Base):
    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String)
    nome_normalizado: Mapped[str] = mapped_column(String, unique=True)
    livros: Mapped[list["Livro"]] = relationship(
        secondary=livros_autores, back_populates="autores"
    )


class Genero(Base):
    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String, unique=True)
    livros: Mapped[list["Livro"]] = relationship(
        secondary=livros_generos, back_populates="generos"
    )


class Livro(Base):
    __tablename__ = "livros"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String)
    # Títulos iguais são permitidos quando o conjunto de autores é diferente.
    titulo_normalizado: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[StatusLeitura] = mapped_column(
        SqlEnum(
            StatusLeitura,
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda statuses: [status.value for status in statuses],
        )
    )
    autores: Mapped[list[Autor]] = relationship(
        secondary=livros_autores, back_populates="livros"
    )
    generos: Mapped[list[Genero]] = relationship(
        secondary=livros_generos, back_populates="livros"
    )
