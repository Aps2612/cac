"""Step 2: objective-driven selection + archetype cohorting.

The objective decides *who* is relevant and *how* they bucket into archetypes.
Selection + labeling happens in SQL (db/sql/cohort_select.sql); aggregation into
per-cohort summary stats (the brief the LLM strategist reads) happens here.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean

import psycopg
from psycopg.types.json import Jsonb

from app.db import load_sql, query_all

# Human-readable metadata for each archetype the cohorting can produce.
ARCHETYPES: dict[str, dict[str, str]] = {
    "loyal_regular": {
        "name": "Loyal Regulars",
        "description": "Bought 3+ times and active in the last 30 days. Happy and engaged.",
    },
    "lapsing_vip": {
        "name": "Lapsing VIPs",
        "description": "High lifetime spend but no order in 1-5 months. High value slipping away.",
    },
    "at_risk_first_timer": {
        "name": "At-Risk First-Timers",
        "description": "Bought exactly once, 2-11 weeks ago. The make-or-break second-purchase window.",
    },
    "one_and_done": {
        "name": "One-and-Done Buyers",
        "description": "A single purchase over 75 days ago, often acquired on a discount.",
    },
    "repeat_winback": {
        "name": "Repeat Win-Back",
        "description": "Multi-time buyers who have cooled off (1-6 months since last order).",
    },
    "dormant_winback": {
        "name": "Dormant Win-Back",
        "description": "No purchase in 6+ months. Deep re-activation candidates.",
    },
    "recent_nurture": {
        "name": "Recent Nurture",
        "description": "Recent buyers who don't fit another bucket. Nurture gently.",
    },
}

OBJECTIVES: dict[str, dict] = {
    "reactivate_lapsing": {
        "label": "Reactivate lapsing customers and lift repeat-purchase rate",
        "description": (
            "Find customers who have purchased before and are at risk of churning, "
            "and bring them back to a profitable second/third purchase."
        ),
        "sql": "cohort_select.sql",
        # Display order in the dashboard.
        "archetypes": [
            "lapsing_vip",
            "at_risk_first_timer",
            "one_and_done",
            "repeat_winback",
            "dormant_winback",
            "loyal_regular",
            "recent_nurture",
        ],
    }
}


def _f(x) -> float:
    return round(float(x), 2) if x is not None else 0.0


def _cohort_stats(rows: list[dict]) -> dict:
    recency = [r["recency_days"] for r in rows if r["recency_days"] is not None]
    monetary = [r["monetary"] for r in rows if r["monetary"] is not None]
    aov = [r["aov"] for r in rows if r["aov"] is not None]
    clv = [r["predicted_clv"] for r in rows if r["predicted_clv"] is not None]
    dep = [r["discount_dependency"] for r in rows if r["discount_dependency"] is not None]
    cats = Counter(r["top_category"] for r in rows if r["top_category"])
    channels = Counter((r["preferred_channel"] or "none") for r in rows)
    return {
        "size": len(rows),
        "avg_recency_days": _f(mean(recency)) if recency else 0.0,
        "avg_monetary": _f(mean(monetary)) if monetary else 0.0,
        "avg_aov": _f(mean(aov)) if aov else 0.0,
        "avg_predicted_clv": _f(mean(clv)) if clv else 0.0,
        "avg_discount_dependency": _f(mean(dep)) if dep else 0.0,
        "top_categories": [{"category": c, "count": n} for c, n in cats.most_common(3)],
        "channel_mix": dict(channels),
    }


def select_and_cohort(conn: psycopg.Connection, run_id: str, objective: str) -> list[dict]:
    """Select the relevant base for the objective and persist cohorts + members.

    Idempotent: re-running for the same run rebuilds cohort rows and membership.
    Returns a list of cohort summaries (cohort_id, key, name, size, stats).
    """
    spec = OBJECTIVES.get(objective)
    if spec is None:
        raise ValueError(f"Unknown objective: {objective}")

    rows = query_all(conn, load_sql(spec["sql"]))

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["archetype_key"], []).append(row)

    ordered_keys = [k for k in spec["archetypes"] if k in grouped]
    # Include any archetype that showed up but isn't in the display list.
    ordered_keys += [k for k in grouped if k not in ordered_keys]

    summaries: list[dict] = []
    for key in ordered_keys:
        members = grouped[key]
        meta = ARCHETYPES.get(key, {"name": key, "description": ""})
        stats = _cohort_stats(members)

        cohort_row = query_all(
            conn,
            """
            INSERT INTO cohorts (run_id, key, name, description, size, stats)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, key) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                size = EXCLUDED.size,
                stats = EXCLUDED.stats
            RETURNING cohort_id
            """,
            (run_id, key, meta["name"], meta["description"], stats["size"], Jsonb(stats)),
        )
        cohort_id = cohort_row[0]["cohort_id"]

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO cohort_members (run_id, cohort_id, customer_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (run_id, customer_id) DO UPDATE SET cohort_id = EXCLUDED.cohort_id
                """,
                [(run_id, cohort_id, m["customer_id"]) for m in members],
            )

        summaries.append(
            {"cohort_id": str(cohort_id), "key": key, "name": meta["name"], "size": stats["size"], "stats": stats}
        )

    return summaries
