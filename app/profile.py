"""STEP 2 — build an understanding of each customer.

One pass turns raw orders into RFM, a second derives the human traits the rest of
the system reasons about: lifecycle, buyer type, preferred channel, reorder cycle,
and a baseline buy probability. Pure SQL, no per-customer Python.
"""

from __future__ import annotations

from .db import connect

# Typical days between reorders per product (consumables cycle faster).
_CYCLE = {
    "vitamin-C serum": 45, "cleanser": 50, "moisturiser": 55,
    "sunscreen": 60, "toner": 50, "retinol": 45,
}
# Build the reorder-cycle lookup as a plain CASE (robust to spaces in names).
_CYCLE_CASE = "CASE top_category " + \
    " ".join(f"WHEN '{k}' THEN {v}" for k, v in _CYCLE.items()) + " ELSE 90 END"

_RFM = """
INSERT INTO profiles (customer_id, recency_days, order_count, monetary, top_category)
SELECT c.customer_id, r.recency_days,
       COALESCE(r.order_count, 0), COALESCE(r.monetary, 0), tc.category
FROM customers c
LEFT JOIN (
    SELECT customer_id, MIN(days_ago) recency_days,
           COUNT(*) order_count, SUM(amount) monetary
    FROM orders GROUP BY customer_id
) r ON r.customer_id = c.customer_id
LEFT JOIN (
    SELECT customer_id, category FROM (
        SELECT customer_id, category, SUM(amount) s,
               row_number() OVER (PARTITION BY customer_id ORDER BY SUM(amount) DESC) rn
        FROM orders GROUP BY customer_id, category
    ) WHERE rn = 1
) tc ON tc.customer_id = c.customer_id;
"""

_TRAITS = f"""
UPDATE profiles SET
    lifecycle = CASE
        WHEN order_count = 0     THEN 'prospect'
        WHEN recency_days <= 45  THEN 'active'
        WHEN recency_days <= 120 THEN 'drifting'
        ELSE 'gone' END,
    buyer_type = CASE
        WHEN c.price_sensitivity < 0.34 THEN 'full_price'
        WHEN c.price_sensitivity < 0.67 THEN 'mixed'
        ELSE 'discount_seeker' END,
    channel = CASE
        WHEN c.whatsapp_open_rate >= c.email_open_rate THEN 'whatsapp'
        ELSE 'email' END,
    replenish_cycle = ({_CYCLE_CASE}),
    base_prob = max(0.02, min(0.30,
        0.04
        + 0.10 * (60.0 / (60.0 + COALESCE(profiles.recency_days, 999)))
        + 0.10 * max(c.email_open_rate, c.whatsapp_open_rate)))
FROM customers c
WHERE c.customer_id = profiles.customer_id;
"""


def build_profiles() -> int:
    with connect() as conn:
        conn.execute("DELETE FROM profiles")
        conn.execute(_RFM)
        conn.execute(_TRAITS)
        return conn.execute("SELECT count(*) FROM profiles").fetchone()[0]
