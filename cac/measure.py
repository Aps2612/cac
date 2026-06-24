"""Steps 7-8 (simulate + measure).

Simulate: the control group gets only its base purchase odds; the treatment
group gets an uplift proportional to how relevant its offer is. (Production
reads real conversions instead.) Measure: incremental lift = treatment rate
minus held-out control rate, with a two-proportion z-test so we know it's real.
"""

from __future__ import annotations

import math
import sqlite3

from .govern import _frac


def base_prob(recency_days: int | None, email_open_rate: float) -> float:
    r = recency_days if recency_days is not None else 365
    p = 0.04 + 0.10 * math.exp(-r / 100.0) + 0.10 * email_open_rate
    return max(0.02, min(p, 0.30))


def converts(customer_id: str, group: str, recency_days: int | None,
             email_open_rate: float, discount: int) -> bool:
    p = base_prob(recency_days, email_open_rate)
    if group == "treatment":
        p = min(p * (1.6 + (0.4 if discount > 0 else 0.0)), 0.6)
    return _frac("convert", customer_id) < p


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def lift(t_n: int, t_c: int, c_n: int, c_c: int) -> dict:
    tr = t_c / t_n if t_n else 0.0
    cr = c_c / c_n if c_n else 0.0
    abs_lift = tr - cr
    p_value = 1.0
    if t_n and c_n:
        pool = (t_c + c_c) / (t_n + c_n)
        se = math.sqrt(pool * (1 - pool) * (1 / t_n + 1 / c_n))
        if se > 0:
            p_value = 2 * (1 - _normal_cdf(abs(abs_lift / se)))
    return {"t_n": t_n, "t_c": t_c, "c_n": c_n, "c_c": c_c,
            "treat_rate": tr, "ctrl_rate": cr, "abs_lift": abs_lift, "p_value": p_value}


def measure(conn: sqlite3.Connection, run_id: str) -> dict:
    """Compute overall + per-cohort lift, persist to ``measurements``, return summary."""
    def counts(where: str, params: tuple) -> dict:
        rows = conn.execute(
            f"""SELECT holdout_group, COUNT(*) AS n, SUM(converted) AS c
                FROM decisions WHERE run_id = ? AND {where} GROUP BY holdout_group""",
            (run_id, *params),
        ).fetchall()
        return {r["holdout_group"]: (r["n"], r["c"] or 0) for r in rows}

    def from_counts(d: dict) -> dict:
        t = d.get("treatment", (0, 0))
        c = d.get("control", (0, 0))
        return lift(t[0], t[1], c[0], c[1])

    def as_row(scope: str, label: str, m: dict) -> tuple:
        return (run_id, scope, label, m["t_n"], m["t_c"], m["c_n"], m["c_c"],
                round(m["treat_rate"], 5), round(m["ctrl_rate"], 5),
                round(m["abs_lift"], 5), round(m["p_value"], 6))

    overall = from_counts(counts("1 = 1", ()))
    rows = [as_row("overall", "All cohorts", overall)]
    per_cohort = []
    for r in conn.execute("SELECT DISTINCT cohort FROM decisions WHERE run_id = ?", (run_id,)):
        m = from_counts(counts("cohort = ?", (r["cohort"],)))
        if m["t_n"] == 0:
            continue
        rows.append(as_row("cohort", r["cohort"], m))
        per_cohort.append((r["cohort"], m))

    conn.execute("DELETE FROM measurements WHERE run_id = ?", (run_id,))
    conn.executemany(
        """INSERT INTO measurements
           (run_id, scope, label, t_n, t_c, c_n, c_c, treat_rate, ctrl_rate, abs_lift, p_value)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return {"overall": overall, "per_cohort": per_cohort}
