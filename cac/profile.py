"""Step 2 (profile): SQL contextual logic.

A single aggregation turns the raw ``orders`` into one clean RFM row per
customer (Recency, Frequency, Monetary + favorite category). This is the kind
of set-based work a database is best at.
"""

from __future__ import annotations

import sqlite3

PROFILE_SQL = """
INSERT INTO customer_profiles (customer_id, recency_days, order_count, monetary, top_category)
SELECT
    c.customer_id,
    MIN(o.days_ago)             AS recency_days,   -- NULL when no orders
    COUNT(o.order_id)           AS order_count,
    COALESCE(SUM(o.amount), 0)  AS monetary,
    (
        SELECT o2.category
        FROM orders o2
        WHERE o2.customer_id = c.customer_id
        GROUP BY o2.category
        ORDER BY SUM(o2.amount) DESC
        LIMIT 1
    )                           AS top_category
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id
"""


def build_profiles(conn: sqlite3.Connection) -> int:
    """Rebuild customer_profiles from orders. Idempotent."""
    conn.execute("DELETE FROM customer_profiles")
    conn.execute(PROFILE_SQL)
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM customer_profiles").fetchone()[0]
