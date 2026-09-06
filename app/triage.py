"""STEP 3 — each day, pick who's worth contacting.

Most customers need nothing today. Cheap SQL keeps only those with a real reason,
and applies the safety gate up front (consent, not opted out, under the daily
frequency cap). Everyone else is dropped before any AI cost is spent.
"""

from __future__ import annotations

from . import config
from .db import connect

# First matching reason wins (most actionable first).
# Narrow "today" windows: most customers have no reason on any given day, so the
# shortlist stays small (a few percent) -- that's where the cost savings come from.
_REASON = """
CASE
    WHEN c.abandoned_cart = 1 THEN 'abandoned_cart'
    WHEN profiles.order_count > 0
         AND profiles.recency_days >= profiles.replenish_cycle
         AND profiles.recency_days <= profiles.replenish_cycle * 1.12 THEN 'replenishment_due'
    WHEN profiles.order_count >= 2
         AND profiles.recency_days BETWEEN 88 AND 104                 THEN 'gone_quiet'
    ELSE NULL
END
"""


def _vip_threshold(conn) -> float:
    """Spend cut-off for a rare VIP = the VIP_PERCENTILE of buyers, by rank."""
    buyers = conn.execute(
        "SELECT count(*) FROM profiles WHERE order_count > 0").fetchone()[0]
    if not buyers:
        return 0.0
    offset = int(config.VIP_PERCENTILE * buyers)
    offset = min(offset, buyers - 1)
    row = conn.execute(
        "SELECT monetary FROM profiles WHERE order_count > 0 "
        "ORDER BY monetary LIMIT 1 OFFSET ?", (offset,)).fetchone()
    return row[0] if row else 0.0


def shortlist() -> dict:
    with connect() as conn:
        vip_cut = _vip_threshold(conn)
        conn.execute(
            f"""
            UPDATE profiles SET
                reason = ({_REASON}),
                is_vip = (profiles.monetary >= ? AND profiles.order_count > 0),
                on_shortlist = (
                    ({_REASON}) IS NOT NULL
                    AND c.opted_out = 0
                    AND (c.consent_email = 1 OR c.consent_whatsapp = 1)
                    AND c.messages_today < ?
                )
            FROM customers c
            WHERE c.customer_id = profiles.customer_id
            """,
            (vip_cut, config.MAX_MESSAGES_PER_DAY),
        )
        total = conn.execute("SELECT count(*) FROM profiles").fetchone()[0]
        short = conn.execute(
            "SELECT count(*) FROM profiles WHERE on_shortlist = 1").fetchone()[0]
        vips = conn.execute(
            "SELECT count(*) FROM profiles WHERE on_shortlist = 1 AND is_vip = 1").fetchone()[0]
        by_reason = {r[0]: r[1] for r in conn.execute(
            "SELECT reason, count(*) FROM profiles WHERE on_shortlist = 1 GROUP BY reason")}
    pct = round(100.0 * short / total, 2) if total else 0.0
    return {"shortlist": short, "shortlist_pct": pct, "vips": vips,
            "by_reason": by_reason, "vip_threshold": round(vip_cut, 2)}
