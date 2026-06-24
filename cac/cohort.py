"""Step 3 (cohort): the RFM ladder.

The first rule that matches wins, so every targeted customer lands in exactly
one archetype. Only customers with >=1 order are relevant to the
"reactivate lapsing" objective; prospects (0 orders) are skipped.
"""

from __future__ import annotations

import sqlite3

ARCHETYPES = [
    "loyal_regular",
    "lapsing_vip",
    "at_risk_first_timer",
    "one_and_done",
    "repeat_winback",
    "dormant_winback",
    "recent_nurture",
]


def cohort_of(order_count: int, recency_days: int | None, monetary: float, vip_spend: float) -> str | None:
    if not order_count:
        return None                                       # prospect: not targeted
    if order_count >= 3 and recency_days <= 30:
        return "loyal_regular"
    if monetary >= vip_spend and 31 <= recency_days <= 150:
        return "lapsing_vip"
    if order_count == 1 and 14 <= recency_days <= 75:
        return "at_risk_first_timer"
    if order_count == 1 and recency_days > 75:
        return "one_and_done"
    if order_count >= 2 and 31 <= recency_days <= 180:
        return "repeat_winback"
    if recency_days > 180:
        return "dormant_winback"
    return "recent_nurture"


def vip_threshold(conn: sqlite3.Connection) -> float:
    """The VIP spend bar = 75th percentile of buyer spend (adapts to the data)."""
    spends = [r[0] for r in conn.execute(
        "SELECT monetary FROM customer_profiles WHERE order_count > 0 ORDER BY monetary"
    ).fetchall()]
    return spends[int(0.75 * len(spends))] if spends else 0.0
