"""The database: one SQLite file, the whole schema, and tiny helpers.

SQLite means zero setup — no server, no passwords, no connection pool. Every step
opens a connection, runs one or two set-based statements, and closes. Simple.
"""

from __future__ import annotations

import sqlite3

from .config import DB_PATH

SCHEMA = """
-- STEP 1: the brand's raw data
CREATE TABLE IF NOT EXISTS customers (
    customer_id       INTEGER PRIMARY KEY,
    name              TEXT    NOT NULL,
    signup_days_ago   INTEGER NOT NULL,
    email_open_rate   REAL    NOT NULL,
    whatsapp_open_rate REAL   NOT NULL,
    price_sensitivity REAL    NOT NULL,   -- 0 = full-price buyer .. 1 = discount seeker
    consent_email     INTEGER NOT NULL,
    consent_whatsapp  INTEGER NOT NULL,
    opted_out         INTEGER NOT NULL,
    abandoned_cart    INTEGER NOT NULL DEFAULT 0,
    messages_today    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL,
    days_ago     INTEGER NOT NULL,
    amount       REAL    NOT NULL,
    category     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);

-- STEPS 2-4: one wide row per customer, each step fills its own columns
CREATE TABLE IF NOT EXISTS profiles (
    customer_id     INTEGER PRIMARY KEY,
    recency_days    INTEGER,
    order_count     INTEGER NOT NULL DEFAULT 0,
    monetary        REAL    NOT NULL DEFAULT 0,
    top_category    TEXT,
    lifecycle       TEXT,                 -- prospect | active | drifting | gone
    buyer_type      TEXT,                 -- full_price | mixed | discount_seeker
    channel         TEXT,                 -- email | whatsapp (whichever they read)
    replenish_cycle INTEGER,              -- expected days between reorders
    base_prob       REAL,                 -- chance they buy if we do nothing
    reason          TEXT,                 -- why contact today (NULL = no reason)
    on_shortlist    INTEGER NOT NULL DEFAULT 0,
    is_vip          INTEGER NOT NULL DEFAULT 0,
    plan_key        TEXT,
    door            TEXT                  -- door1 | door2 | door3
);
CREATE INDEX IF NOT EXISTS idx_profiles_plan ON profiles(plan_key);

-- STEP 4: the persistent "saved plans" cache (survives across runs)
CREATE TABLE IF NOT EXISTS plans (
    plan_key    TEXT PRIMARY KEY,
    scope       TEXT NOT NULL,            -- group | vip
    reason      TEXT NOT NULL,
    buyer_type  TEXT NOT NULL,
    suppress    INTEGER NOT NULL DEFAULT 0,
    discount    INTEGER NOT NULL DEFAULT 0,
    channel_rule TEXT NOT NULL DEFAULT 'auto',
    headline    TEXT NOT NULL DEFAULT '',
    body        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL DEFAULT 'rule',  -- llm | rule
    reused      INTEGER NOT NULL DEFAULT 0,
    created_run TEXT
);

-- STEPS 5-6: one decision per shortlisted customer per run
CREATE TABLE IF NOT EXISTS decisions (
    run_id       TEXT NOT NULL,
    customer_id  INTEGER NOT NULL,
    reason       TEXT NOT NULL,
    door         TEXT NOT NULL,
    plan_key     TEXT NOT NULL,
    grp          TEXT NOT NULL,           -- treatment | control | blocked
    block_reason TEXT,
    channel      TEXT,
    discount     INTEGER NOT NULL DEFAULT 0,
    message      TEXT,
    offer_code   TEXT,
    converted    INTEGER NOT NULL DEFAULT 0,
    revenue      REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (run_id, customer_id)
);
CREATE INDEX IF NOT EXISTS idx_decisions_run ON decisions(run_id);

-- STEP 7: the lift scoreboard
CREATE TABLE IF NOT EXISTS measurements (
    run_id     TEXT NOT NULL,
    scope      TEXT NOT NULL,             -- overall | reason
    label      TEXT NOT NULL,
    t_n INTEGER, t_c INTEGER, c_n INTEGER, c_c INTEGER,
    treat_rate REAL, ctrl_rate REAL, abs_lift REAL, p_value REAL,
    PRIMARY KEY (run_id, scope, label)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id     TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    params     TEXT NOT NULL DEFAULT '{}'
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def reset_db() -> None:
    """Wipe everything, including the saved-plans cache, and rebuild empty tables."""
    with connect() as conn:
        for t in ("measurements", "decisions", "plans", "profiles",
                  "orders", "customers", "runs"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.executescript(SCHEMA)


def counts() -> dict[str, int]:
    with connect() as conn:
        return {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                for t in ("customers", "orders", "profiles", "plans", "decisions")}
