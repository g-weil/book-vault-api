from enum import Enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum as SqlEnum, ForeignKey, JSON, String, Table, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class StatusLeitura(str, Enum):
    QUERO_LER = "Quero ler"
    LENDO = "Lendo"
    LIDO = "Lido"
    RELENDO = "Relendo"
    ABANDONADO = "Abandonado"


class PapelUsuario(str, Enum):
    USUARIO = "usuario"
    ADMINISTRADOR = "administrador"


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("NOT ativo OR senha_hash IS NOT NULL", name="usuario_ativo_exige_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(320))
    email_normalizado: Mapped[str] = mapped_column(String(320), unique=True)
    # Conta ainda não ativada pode ficar sem senha; nunca guardar senha em texto.
    senha_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=False)
    papel: Mapped[PapelUsuario] = mapped_column(SqlEnum(
        PapelUsuario, native_enum=False, create_constraint=True,
        name="papel_usuario", values_callable=lambda papeis: [papel.value for papel in papeis],
    ), default=PapelUsuario.USUARIO)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    biblioteca: Mapped[list["BibliotecaUsuario"]] = relationship(back_populates="usuario")


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
    capa_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # Campo legado preservado durante a transição. As rotas atuais ainda o usam;
    # após adaptar autenticação e endpoints, o status pessoal será o do vínculo.
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
    bibliotecas: Mapped[list["BibliotecaUsuario"]] = relationship(back_populates="livro")


class BibliotecaUsuario(Base):
    __tablename__ = "biblioteca_usuario"
    __table_args__ = (
        UniqueConstraint("usuario_id", "livro_id", name="uq_biblioteca_usuario_livro"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    livro_id: Mapped[int] = mapped_column(ForeignKey("livros.id"), index=True)
    status: Mapped[StatusLeitura] = mapped_column(SqlEnum(
        StatusLeitura, native_enum=False, create_constraint=True, validate_strings=True,
        name="status_biblioteca", values_callable=lambda statuses: [status.value for status in statuses],
    ))
    adicionado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Somente diferenças locais: ausência de chave herda o catálogo; capa_url=null
    # remove a imagem apenas desta biblioteca. A API futura validará esses campos.
    personalizacoes: Mapped[dict] = mapped_column(JSON, default=dict)
    usuario: Mapped[Usuario] = relationship(back_populates="biblioteca")
    livro: Mapped[Livro] = relationship(back_populates="bibliotecas")
