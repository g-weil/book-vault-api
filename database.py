from pathlib import Path
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_PATH = Path(__file__).resolve().parent / "book_vault.db"
engine = create_engine(
    f"sqlite:///{DATABASE_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def habilitar_chaves_estrangeiras(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine)


def preparar_banco() -> None:
    Base.metadata.create_all(bind=engine)
    # create_all não altera tabelas existentes. Esta mudança apenas acrescenta
    # uma coluna opcional; livros antigos continuam salvos com capa_url = NULL.
    with engine.begin() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        colunas = {linha[1] for linha in connection.exec_driver_sql("PRAGMA table_info(livros)")}
        if "capa_url" not in colunas:
            connection.exec_driver_sql("ALTER TABLE livros ADD COLUMN capa_url VARCHAR")


def obter_sessao() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
