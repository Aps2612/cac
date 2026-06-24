"""SQLite access + schema.

A real relational database with real SQL, but file-based and dependency-free
(Python's built-in ``sqlite3``). The whole DB is a single ``cac.db`` file in the
project root, so there's nothing to install or run.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "cac.db"

SCHEMA = """
-- Raw layer: what a brand's systems would stream in.
CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,
    signup_days_ago INTEGER NOT NULL,
    email_open_rate REAL    NOT NULL,
    consent_email   INTEGER NOT NULL,   -- 0/1
    opted_out       INTEGER NOT NULL    -- 0/1
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    days_ago    INTEGER NOT NULL,
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);

-- Profile layer: one clean RFM row per customer, built from orders by SQL.
CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id  TEXT PRIMARY KEY REFERENCES customers(customer_id),
    recency_days INTEGER,             -- days since last order (NULL = never bought)
    order_count  INTEGER NOT NULL,
    monetary     REAL    NOT NULL,
    top_category TEXT
);

-- Decision layer: one decision per targeted customer per run.
CREATE TABLE IF NOT EXISTS decisions (
    run_id        TEXT NOT NULL,
    customer_id   TEXT NOT NULL,
    cohort        TEXT NOT NULL,
    holdout_group TEXT NOT NULL,       -- treatment | control | suppressed
    discount      INTEGER NOT NULL,
    offer_code    TEXT,
    converted     INTEGER NOT NULL DEFAULT 0,
    revenue       REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (run_id, customer_id)
);

-- Measurement layer: the lift scoreboard per run.
CREATE TABLE IF NOT EXISTS measurements (
    run_id     TEXT NOT NULL,
    scope      TEXT NOT NULL,          -- overall | cohort
    label      TEXT NOT NULL,
    t_n        INTEGER, t_c INTEGER,
    c_n        INTEGER, c_c INTEGER,
    treat_rate REAL, ctrl_rate REAL, abs_lift REAL, p_value REAL
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
