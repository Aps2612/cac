"""Orchestrate one decisioning run over the seeded data and persist the results.

profile -> cohort -> strategy -> personalize/govern -> simulate -> measure.
"""

from __future__ import annotations

import uuid

from .cohort import cohort_of, vip_threshold
from .db import connect
from .govern import assign_group, offer_code
from .measure import converts, measure
from .profile import build_profiles
from .strategy import STRATEGY


def run() -> dict:
    run_id = uuid.uuid4().hex[:8]
    conn = connect()

    build_profiles(conn)
    vip = vip_threshold(conn)

    profiles = conn.execute(
        """SELECT p.customer_id, p.recency_days, p.order_count, p.monetary, p.top_category,
                  c.email_open_rate, c.consent_email, c.opted_out
           FROM customer_profiles p
           JOIN customers c ON c.customer_id = p.customer_id"""
    ).fetchall()

    decisions: list[tuple] = []
    for r in profiles:
        cohort = cohort_of(r["order_count"], r["recency_days"], r["monetary"], vip)
        if cohort is None:
            continue
        strat = STRATEGY[cohort]
        group = assign_group(r["customer_id"], strat, r["consent_email"], r["opted_out"])
        code = None if strat.suppress else offer_code(cohort, r["customer_id"])

        converted, revenue = 0, 0.0
        if group in ("treatment", "control") and converts(
            r["customer_id"], group, r["recency_days"], r["email_open_rate"], strat.discount
        ):
            converted = 1
            revenue = round((r["monetary"] / max(r["order_count"], 1)) or 50.0, 2)

        decisions.append((run_id, r["customer_id"], cohort, group,
                          strat.discount, code, converted, revenue))

    conn.execute("DELETE FROM decisions WHERE run_id = ?", (run_id,))
    conn.executemany(
        "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", decisions
    )
    summary = measure(conn, run_id)
    conn.commit()
    conn.close()
    return {"run_id": run_id, "targeted": len(decisions), "overall": summary["overall"]}
