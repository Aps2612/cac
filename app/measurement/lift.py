"""Measurement (part 2): incremental lift, the honest scoreboard.

Compares the treatment group against the held-out control with a two-proportion
z-test. This is real incremental lift (what the program *caused*), not last-touch
attribution (which would credit the program for purchases that would have happened
anyway).
"""

from __future__ import annotations

import math

import psycopg

from app.db import query_all


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def compute_lift(
    treatment_n: int,
    treatment_conv: int,
    control_n: int,
    control_conv: int,
    avg_rev_per_conversion: float,
) -> dict:
    tr = treatment_conv / treatment_n if treatment_n else 0.0
    cr = control_conv / control_n if control_n else 0.0
    abs_lift = tr - cr
    rel_lift = (abs_lift / cr) if cr > 0 else 0.0

    # Two-proportion z-test (pooled) for the p-value.
    p_value = 1.0
    if treatment_n and control_n:
        p_pool = (treatment_conv + control_conv) / (treatment_n + control_n)
        se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / treatment_n + 1 / control_n))
        if se_pool > 0:
            z = abs_lift / se_pool
            p_value = 2 * (1 - _phi(abs(z)))

    # 95% CI on the absolute difference (unpooled SE).
    ci_low = ci_high = abs_lift
    if treatment_n and control_n:
        se_diff = math.sqrt(tr * (1 - tr) / treatment_n + cr * (1 - cr) / control_n)
        ci_low = abs_lift - 1.96 * se_diff
        ci_high = abs_lift + 1.96 * se_diff

    revenue_lift = abs_lift * treatment_n * avg_rev_per_conversion

    return {
        "treatment_n": treatment_n,
        "treatment_conv": treatment_conv,
        "control_n": control_n,
        "control_conv": control_conv,
        "treatment_rate": round(tr, 5),
        "control_rate": round(cr, 5),
        "abs_lift": round(abs_lift, 5),
        "rel_lift": round(rel_lift, 4),
        "ci_low": round(ci_low, 5),
        "ci_high": round(ci_high, 5),
        "p_value": round(p_value, 6),
        "revenue_lift": round(revenue_lift, 2),
    }


def measure(conn: psycopg.Connection, run_id: str) -> dict:
    """Compute overall + per-cohort lift, persist to `measurements`, return a summary."""
    avg_row = query_all(
        conn,
        "SELECT coalesce(avg(revenue), 0) AS a FROM outcomes WHERE run_id = %s AND converted",
        (run_id,),
    )
    avg_rev = float(avg_row[0]["a"]) if avg_row else 0.0

    def _counts(where_sql: str, params: tuple) -> dict[str, dict]:
        rows = query_all(
            conn,
            f"""
            SELECT holdout_group, count(*) AS n, count(*) FILTER (WHERE converted) AS conv
            FROM outcomes WHERE {where_sql} GROUP BY holdout_group
            """,
            params,
        )
        return {r["holdout_group"]: {"n": r["n"], "conv": r["conv"]} for r in rows}

    overall = _counts("run_id = %s", (run_id,))
    overall_lift = compute_lift(
        overall.get("treatment", {}).get("n", 0), overall.get("treatment", {}).get("conv", 0),
        overall.get("control", {}).get("n", 0), overall.get("control", {}).get("conv", 0),
        avg_rev,
    )

    cohorts = query_all(
        conn,
        """
        SELECT c.cohort_id, c.key, c.name
        FROM cohorts c
        WHERE c.run_id = %s
          AND EXISTS (SELECT 1 FROM outcomes o WHERE o.cohort_id = c.cohort_id)
        ORDER BY c.size DESC
        """,
        (run_id,),
    )

    rows_to_store: list[tuple] = []
    rows_to_store.append((run_id, None, "overall", "All cohorts", *_as_tuple(overall_lift)))

    per_cohort = []
    for c in cohorts:
        cc = _counts("cohort_id = %s", (c["cohort_id"],))
        lift = compute_lift(
            cc.get("treatment", {}).get("n", 0), cc.get("treatment", {}).get("conv", 0),
            cc.get("control", {}).get("n", 0), cc.get("control", {}).get("conv", 0),
            avg_rev,
        )
        rows_to_store.append((run_id, c["cohort_id"], "cohort", c["name"], *_as_tuple(lift)))
        per_cohort.append({"key": c["key"], "name": c["name"], **lift})

    conn.execute("DELETE FROM measurements WHERE run_id = %s", (run_id,))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO measurements
                (run_id, cohort_id, scope, label,
                 treatment_n, treatment_conv, control_n, control_conv,
                 treatment_rate, control_rate, abs_lift, rel_lift, ci_low, ci_high, p_value, revenue_lift)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows_to_store,
        )

    return {"overall": overall_lift, "per_cohort": per_cohort, "avg_revenue_per_conversion": round(avg_rev, 2)}


def _as_tuple(lift: dict) -> tuple:
    return (
        lift["treatment_n"], lift["treatment_conv"], lift["control_n"], lift["control_conv"],
        lift["treatment_rate"], lift["control_rate"], lift["abs_lift"], lift["rel_lift"],
        lift["ci_low"], lift["ci_high"], lift["p_value"], lift["revenue_lift"],
    )
