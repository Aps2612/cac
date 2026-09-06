"""STEP 7 — prove it worked.

We always hold back a control group who get nothing. Lift = how much more the
messaged group bought than the control. The two-proportion z-test says whether the
gap is real or just luck. Counts come from SQL; the small stats are done in Python.
"""

from __future__ import annotations

import math

from .db import connect


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def lift(t_n, t_c, c_n, c_c) -> dict:
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


def measure(run_id: str) -> dict:
    with connect() as conn:
        rows = conn.execute(
            """SELECT reason, grp, count(*) n, sum(converted) c
               FROM decisions WHERE run_id = ? GROUP BY reason, grp""",
            (run_id,)).fetchall()

        by_reason: dict[str, dict[str, tuple[int, int]]] = {}
        overall = {"treatment": [0, 0], "control": [0, 0]}
        for reason, grp, n, c in rows:
            by_reason.setdefault(reason, {})[grp] = (n, c or 0)
            if grp in overall:
                overall[grp][0] += n
                overall[grp][1] += c or 0

        def row(scope, label, m):
            return (run_id, scope, label, m["t_n"], m["t_c"], m["c_n"], m["c_c"],
                    round(m["treat_rate"], 5), round(m["ctrl_rate"], 5),
                    round(m["abs_lift"], 5), round(m["p_value"], 6))

        overall_m = lift(*overall["treatment"], *overall["control"])
        out = [row("overall", "All reasons", overall_m)]
        per_reason = []
        for reason, g in sorted(by_reason.items()):
            t, c = g.get("treatment", (0, 0)), g.get("control", (0, 0))
            m = lift(t[0], t[1], c[0], c[1])
            if m["t_n"] or m["c_n"]:
                out.append(row("reason", reason, m))
                per_reason.append({"reason": reason, **m})

        conn.execute("DELETE FROM measurements WHERE run_id = ?", (run_id,))
        conn.executemany(
            "INSERT INTO measurements VALUES (?,?,?,?,?,?,?,?,?,?,?)", out)

    return {"overall": overall_m, "per_reason": per_reason}
