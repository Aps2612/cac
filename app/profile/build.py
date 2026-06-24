"""Step 1 (profile): run the SQL contextual logic to (re)build per-customer profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import psycopg

from app.db import connection, execute, load_sql, query_all, query_one


def build_profiles(conn: psycopg.Connection, as_of: datetime) -> int:
    """Rebuild customer_profiles from the raw layer. Idempotent for a given as_of."""
    sql = load_sql("profile_build.sql")
    execute(conn, sql, {"as_of": as_of})
    row = query_one(conn, "SELECT count(*) AS n FROM customer_profiles")
    return int(row["n"]) if row else 0


def profile_summary(conn: psycopg.Connection) -> dict:
    """A quick distribution snapshot, useful for the pipeline log and dashboard."""
    by_stage = query_all(
        conn,
        """
        SELECT lifecycle_stage, count(*) AS n
        FROM customer_profiles
        GROUP BY lifecycle_stage
        ORDER BY n DESC
        """,
    )
    totals = query_one(
        conn,
        """
        SELECT
            count(*) AS customers,
            count(*) FILTER (WHERE is_repeat) AS repeat_customers,
            round(avg(aov) FILTER (WHERE order_count > 0), 2) AS avg_aov,
            round(avg(recency_days) FILTER (WHERE order_count > 0), 1) AS avg_recency_days
        FROM customer_profiles
        """,
    )
    totals = totals or {}
    totals = {k: (float(v) if isinstance(v, Decimal) else v) for k, v in totals.items()}
    return {"by_stage": {r["lifecycle_stage"]: r["n"] for r in by_stage}, "totals": totals}


def run(as_of: datetime | None = None) -> dict:
    """Standalone profile build against a fresh connection (used for ad-hoc runs/tests)."""
    as_of = as_of or datetime.now(timezone.utc)
    with connection() as conn:
        n = build_profiles(conn, as_of)
        summary = profile_summary(conn)
    return {"profiles": n, **summary}
