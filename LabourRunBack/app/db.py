from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import Settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(settings: Settings) -> sqlite3.Connection:
    if settings.db_path != ":memory:":
        Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        settings.db_path,
        timeout=10.0,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    if settings.db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn(settings: Settings) -> Iterator[sqlite3.Connection]:
    conn = connect(settings)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(settings: Settings) -> Iterator[sqlite3.Connection]:
    conn = connect(settings)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_db(settings: Settings) -> None:
    conn = connect(settings)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _ensure_column(
            conn,
            "activities",
            "updated_by_admin_id",
            "TEXT",
        )
        _ensure_column(
            conn,
            "challenges",
            "updated_by_admin_id",
            "TEXT",
        )
        from .seed import seed

        seed(conn)
    finally:
        conn.close()
