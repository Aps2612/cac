"""Database access and a tiny migration runner.

We deliberately keep this thin: psycopg 3 + raw SQL. The interesting
"contextual logic" lives in db/sql/*.sql, not in an ORM.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator, Sequence
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import MIGRATIONS_DIR, SQL_DIR, get_settings


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def to_jsonb(obj: Any) -> Jsonb:
    """Wrap a Python object as JSONB, tolerating Decimal/datetime/UUID/set values."""
    return Jsonb(obj, dumps=lambda o: json.dumps(o, default=_json_default))


def connect() -> psycopg.Connection:
    """Open a new connection with dict rows. Caller is responsible for closing."""
    settings = get_settings()
    return psycopg.connect(settings.database_url, row_factory=dict_row, autocommit=False)


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(conn: psycopg.Connection, sql: str, params: Sequence[Any] | dict | None = None) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(conn: psycopg.Connection, sql: str, params: Sequence[Any] | dict | None = None) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(conn: psycopg.Connection, sql: str, params: Sequence[Any] | dict | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def copy_rows(
    conn: psycopg.Connection,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> int:
    """Fast bulk insert via COPY. Returns the number of rows written."""
    if not rows:
        return 0
    cols = ", ".join(columns)
    written = 0
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({cols}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(row)
                written += 1
    return written


def load_sql(name: str) -> str:
    """Read a SQL file from db/sql by file name."""
    path = SQL_DIR / name
    return path.read_text(encoding="utf-8")


# --- Migrations ---------------------------------------------------------------

_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
"""


def _migration_files() -> list[Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))


def run_migrations(reset: bool = False) -> list[str]:
    """Apply pending migrations in filename order. Idempotent.

    Returns the list of filenames that were applied during this call.
    """
    applied: list[str] = []
    with connection() as conn:
        if reset:
            execute(conn, "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
        execute(conn, _MIGRATIONS_TABLE)
        done = {row["filename"] for row in query_all(conn, "SELECT filename FROM schema_migrations")}
        for path in _migration_files():
            if path.name in done:
                continue
            sql = path.read_text(encoding="utf-8")
            execute(conn, sql)
            execute(
                conn,
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (path.name,),
            )
            applied.append(path.name)
    return applied


def healthcheck() -> bool:
    try:
        with connection() as conn:
            query_one(conn, "SELECT 1 AS ok")
        return True
    except Exception:
        return False
