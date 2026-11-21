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


def _ensure_coupon_ledger_reward_type(
    conn: sqlite3.Connection,
) -> None:
    row = conn.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'coupon_ledger'
        """
    ).fetchone()
    table_sql = (row["sql"] or "").lower() if row else ""
    if row is None or "'reward'" in table_sql:
        return

    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "ALTER TABLE coupon_ledger RENAME TO coupon_ledger_old"
        )
        conn.execute(
            """
            CREATE TABLE coupon_ledger (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                type TEXT NOT NULL
                    CHECK (type IN (
                        'exchange', 'reward', 'challenge_deposit',
                        'refund', 'adjust'
                    )),
                amount_cents INTEGER NOT NULL,
                balance_after_cents INTEGER NOT NULL,
                ref_type TEXT,
                ref_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO coupon_ledger
                (id, user_id, type, amount_cents, balance_after_cents,
                 ref_type, ref_id, created_at)
            SELECT
                id, user_id, type, amount_cents, balance_after_cents,
                ref_type, ref_id, created_at
            FROM coupon_ledger_old
            """
        )
        conn.execute("DROP TABLE coupon_ledger_old")
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_ledger_user_created
            ON coupon_ledger(user_id, created_at DESC)
            """
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def init_db(settings: Settings) -> None:
    conn = connect(settings)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _ensure_coupon_ledger_reward_type(conn)
        _ensure_column(
            conn,
            "activities",
            "image_url",
            "TEXT",
        )
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
