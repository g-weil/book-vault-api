from pathlib import Path
from collections.abc import Iterator
from contextlib import contextmanager
import os

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Connection, URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_PATH = Path(
    os.environ.get("BOOK_VAULT_DB_PATH", str(Path(__file__).resolve().parent / "book_vault.db"))
).expanduser().resolve()
def habilitar_chaves_estrangeiras(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")


def criar_engine(url: str | URL):
    endereco = make_url(url)
    if endereco.drivername in {"postgres", "postgresql"}:
        endereco = endereco.set(drivername="postgresql+psycopg")

    if endereco.get_backend_name() == "sqlite":
        if endereco.database and endereco.database != ":memory:":
            Path(endereco.database).parent.mkdir(parents=True, exist_ok=True)
        conexao = create_engine(endereco, connect_args={"check_same_thread": False})
        event.listen(conexao, "connect", habilitar_chaves_estrangeiras)
        return conexao

    if endereco.drivername == "postgresql+psycopg":
        return create_engine(endereco, pool_pre_ping=True, isolation_level="READ COMMITTED")

    raise ValueError("Use SQLite ou PostgreSQL com o driver psycopg na DATABASE_URL.")


def obter_url_banco() -> str | URL:
    # URL explícita tem prioridade. No Compose, construir com a senha original
    # evita erros de codificação quando ela contém @, #, / ou outros caracteres.
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if os.environ.get("POSTGRES_HOST"):
        obrigatorias = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
        if any(not os.environ.get(nome) for nome in obrigatorias):
            raise ValueError("Defina POSTGRES_USER, POSTGRES_PASSWORD e POSTGRES_DB para conectar.")
        return URL.create(
            "postgresql+psycopg",
            username=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            database=os.environ["POSTGRES_DB"],
        )
    return URL.create("sqlite", database=DATABASE_PATH.as_posix())


DATABASE_URL = obter_url_banco()
engine = criar_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def bloquear_escrita(connection: Connection) -> None:
    """Serializa as escritas da aplicação antes de consultar e alterar registros."""
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("BEGIN IMMEDIATE")
    elif connection.dialect.name == "postgresql":
        # Mesma chave em todas as escritas. O commit/rollback libera o bloqueio.
        connection.execute(text("SELECT pg_advisory_xact_lock(:chave)"), {"chave": 19420817})
    else:
        raise ValueError("Banco não suportado para transações de escrita.")


@contextmanager
def transacao_escrita(session: Session) -> Iterator[None]:
    with session.begin():
        bloquear_escrita(session.connection())
        yield


def preparar_banco() -> None:
    # create_all não altera tabelas existentes. Esta mudança apenas acrescenta
    # uma coluna opcional; livros antigos continuam salvos com capa_url = NULL.
    with engine.begin() as connection:
        bloquear_escrita(connection)
        Base.metadata.create_all(bind=connection)
        colunas = {coluna["name"] for coluna in inspect(connection).get_columns("livros")}
        if "capa_url" not in colunas:
            connection.exec_driver_sql("ALTER TABLE livros ADD COLUMN capa_url VARCHAR")


def obter_sessao() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
