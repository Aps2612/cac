"""Measurement (part 1): simulate outcomes for the treatment and control groups.

In production this layer reads real conversions. For the demo we simulate them with
a deterministic response model so lift is reproducible: every customer has a base
purchase probability from their profile; the treatment group gets an uplift
proportional to how *relevant* their decision was (relevant offer, preferred and
deliverable channel, product in their favorite category). The control group gets
only the base probability - that is what makes the measured lift real.
"""

from __future__ import annotations

import hashlib
import math

import psycopg
from psycopg.types.json import Jsonb  # noqa: F401  (kept for parity with other modules)

from app.config import Settings, get_settings
from app.db import query_all
from app.schemas import OfferType


def _frac(*parts: str) -> float:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return int(digest[:12], 16) / 0xFFFFFFFFFFFF


def base_probability(recency_days: int | None, email_open_rate: float) -> float:
    r = recency_days if recency_days is not None else 365
    p = 0.04 + 0.10 * math.exp(-r / 100.0) + 0.10 * float(email_open_rate or 0)
    return max(0.02, min(p, 0.30))


def relevance_multiplier(decision: dict, profile: dict, product_category: str | None) -> float:
    rel = 0.0
    offer = decision.get("offer") or {}
    if offer.get("type") and offer.get("type") != OfferType.none.value:
        rel += 0.40
    if decision.get("channel") and decision.get("channel") == profile.get("preferred_channel"):
        rel += 0.30
    if product_category and product_category == profile.get("top_category"):
        rel += 0.30
    return 1.0 + rel


def simulate_outcomes(conn: psycopg.Connection, run_id: str, settings: Settings | None = None) -> dict:
    """Generate deterministic outcomes for everyone in the experiment. Idempotent."""
    settings = settings or get_settings()

    catalog = {r["product_id"]: r["category"] for r in query_all(conn, "SELECT product_id, category FROM catalog")}

    rows = query_all(
        conn,
        """
        SELECT d.customer_id, d.cohort_id, d.holdout_group, d.channel, d.product_id, d.offer,
               cp.recency_days, cp.email_open_rate, cp.aov, cp.preferred_channel, cp.top_category
        FROM decisions d
        JOIN customer_profiles cp ON cp.customer_id = d.customer_id
        WHERE d.run_id = %s AND d.holdout_group IN ('treatment', 'control')
        """,
        (run_id,),
    )

    out: list[tuple] = []
    counts = {"treatment": 0, "control": 0, "conversions": 0}
    for d in rows:
        base = base_probability(d["recency_days"], d["email_open_rate"])
        if d["holdout_group"] == "treatment":
            prob = min(base * relevance_multiplier(d, d, catalog.get(d["product_id"])), 0.6)
            counts["treatment"] += 1
        else:
            prob = base
            counts["control"] += 1

        converted = _frac(str(run_id), d["customer_id"], "conv") < prob
        aov = float(d["aov"] or 0) or 50.0
        revenue = round(aov * (0.8 + 0.6 * _frac(str(run_id), d["customer_id"], "rev")), 2) if converted else 0.0
        if converted:
            counts["conversions"] += 1
        out.append((str(run_id), d["customer_id"], d["cohort_id"], d["holdout_group"], converted, revenue))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO outcomes (run_id, customer_id, cohort_id, holdout_group, converted, revenue)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, customer_id) DO UPDATE SET
                holdout_group = EXCLUDED.holdout_group,
                converted = EXCLUDED.converted,
                revenue = EXCLUDED.revenue,
                observed_at = now()
            """,
            out,
        )
    return counts
