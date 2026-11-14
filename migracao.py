"""Backup consistente e cópia única de SQLite para PostgreSQL vazio."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.engine import Engine

from database import Base, bloquear_escrita, criar_engine
import models  # Registra as cinco tabelas e suas dependências.


def ler_registros(backup: Path) -> dict[str, list[dict]]:
    with closing(sqlite3.connect(backup.as_uri() + "?mode=ro", uri=True)) as source:
        source.row_factory = sqlite3.Row
        if source.execute("PRAGMA integrity_check").fetchall()[0][0] != "ok":
            raise ValueError("O backup SQLite não passou na verificação de integridade.")
        if source.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("O SQLite possui relacionamentos inválidos; corrija antes da cópia.")
        registros = {}
        for table in Base.metadata.sorted_tables:
            # Identificadores vêm dos modelos do projeto, nunca da entrada do usuário.
            colunas = {row[1] for row in source.execute(f'PRAGMA table_info("{table.name}")')}
            esperadas = {column.name for column in table.columns}
            ausentes = esperadas - colunas
            if ausentes - ({"capa_url"} if table.name == "livros" else set()):
                raise ValueError(f"Estrutura SQLite incompatível na tabela {table.name}.")
            if colunas - esperadas:
                raise ValueError(f"Colunas não previstas em {table.name}; revisar a migração.")
            ordem = ", ".join(f'"{column.name}"' for column in table.primary_key)
            linhas = source.execute(f'SELECT * FROM "{table.name}" ORDER BY {ordem}')
            registros[table.name] = [
                {column.name: dict(row).get(column.name) for column in table.columns}
                for row in linhas
            ]
        return registros


def conferir_registros(connection, registros: dict[str, list[dict]]) -> None:
    for table in Base.metadata.sorted_tables:
        consulta = select(table).order_by(*table.primary_key.columns)
        recebidos = [
            {key: value.value if isinstance(value, Enum) else value for key, value in row.items()}
            for row in connection.execute(consulta).mappings()
        ]
        if recebidos != registros[table.name]:
            raise ValueError(f"Os registros de {table.name} não conferem com o backup.")


def ajustar_sequencias(connection, registros) -> None:
    quote = connection.dialect.identifier_preparer.quote
    for nome in ("autores", "generos", "livros"):
        sequence = connection.execute(text("""
            SELECT n.nspname, c.relname FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.oid = CAST(pg_get_serial_sequence(:tabela, 'id') AS regclass)
        """), {"tabela": nome}).one()
        proximo = max((row["id"] for row in registros[nome]), default=0) + 1
        # RESTART, ao contrário de setval, participa do rollback da transação.
        identificador = f"{quote(sequence[0])}.{quote(sequence[1])}"
        connection.exec_driver_sql(f"ALTER SEQUENCE {identificador} RESTART WITH {proximo}")


def migrar_sqlite(origem: Path, destino: Engine, diretorio_backup: Path) -> dict:
    origem = origem.expanduser().resolve(strict=True)
    if destino.dialect.name != "postgresql":
        raise ValueError("O destino da transferência deve ser PostgreSQL.")
    diretorio_backup = diretorio_backup.expanduser().resolve()
    diretorio_backup.mkdir(parents=True, exist_ok=True)
    instante = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = diretorio_backup / f"book_vault_{instante}_{uuid4().hex[:8]}.db"

    # Bloqueia escritores SQLite até terminar a cópia. Não modifica os registros.
    with closing(sqlite3.connect(origem.as_uri() + "?mode=rw", uri=True, timeout=5)) as bloqueio:
        bloqueio.execute("BEGIN IMMEDIATE")
        try:
            backup.touch(exist_ok=False)
            with closing(sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True)) as source:
                with closing(sqlite3.connect(backup)) as copia:
                    source.backup(copia)
            registros = ler_registros(backup)
            with destino.begin() as connection:
                bloquear_escrita(connection)
                Base.metadata.create_all(bind=connection)
                nomes = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
                connection.exec_driver_sql(f"LOCK TABLE {nomes} IN EXCLUSIVE MODE")
                for table in Base.metadata.sorted_tables:
                    if connection.execute(select(table).limit(1)).first() is not None:
                        raise ValueError(
                            f"Destino não está vazio ({table.name}). Nada será sobrescrito. "
                            "O backup SQLite foi preservado."
                        )
                for table in Base.metadata.sorted_tables:
                    if registros[table.name]:
                        connection.execute(table.insert(), registros[table.name])
                conferir_registros(connection, registros)
                ajustar_sequencias(connection, registros)
            return {
                "backup": str(backup),
                "registros": {nome: len(linhas) for nome, linhas in registros.items()},
                "comparacao_integral": "confirmada antes do commit",
            }
        finally:
            bloqueio.rollback()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", type=Path, required=True)
    parser.add_argument("--backups", type=Path, default=Path("backups"))
    args = parser.parse_args()
    url = os.environ.get("BOOK_VAULT_MIGRATION_DATABASE_URL")
    if not url:
        parser.error("Defina BOOK_VAULT_MIGRATION_DATABASE_URL para o destino PostgreSQL.")
    destino = criar_engine(url)
    try:
        resultado = migrar_sqlite(args.origem, destino, args.backups)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except Exception as error:
        # Não exibir URL, credenciais ou registros pessoais nos erros do driver.
        mensagem = str(error) if isinstance(error, (ValueError, FileNotFoundError)) else type(error).__name__
        parser.exit(1, f"Transferência não concluída: {mensagem}\n")
    finally:
        destino.dispose()


if __name__ == "__main__":
    main()
