"""FastAPI app + dashboard.

Read endpoints expose the pipeline's output (runs, cohorts + strategies, decisions
with the emitted JSON, suppressions, lift). A POST triggers a fresh run. The dashboard
is a zero-build single-page app served from app/api/static.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.cohort.select import OBJECTIVES
from app.config import STATIC_DIR, get_settings
from app.db import connection, query_all, query_one
from app.pipeline.run import run_pipeline

app = FastAPI(title="CAC Decisioning Layer", version="0.1.0")


@app.get("/api/health")
def health() -> dict:
    ok = query_one_safe("SELECT 1 AS ok") is not None
    return {"ok": ok}


def query_one_safe(sql: str, params: tuple | None = None) -> dict | None:
    try:
        with connection() as conn:
            return query_one(conn, sql, params)
    except Exception:
        return None


@app.get("/api/objectives")
def objectives() -> list[dict]:
    return [{"key": k, "label": v["label"], "description": v["description"]} for k, v in OBJECTIVES.items()]


@app.get("/api/stats")
def stats() -> dict:
    with connection() as conn:
        return query_one(
            conn,
            """
            SELECT
                (SELECT count(*) FROM customers)          AS customers,
                (SELECT count(*) FROM customer_profiles)  AS profiles,
                (SELECT count(*) FROM catalog)            AS products,
                (SELECT count(*) FROM orders)             AS orders
            """,
        ) or {}


@app.get("/api/runs")
def runs() -> list[dict]:
    with connection() as conn:
        return query_all(
            conn,
            """
            SELECT run_id, objective, status, current_stage, params, stats, created_at, finished_at
            FROM pipeline_runs ORDER BY created_at DESC LIMIT 25
            """,
        )


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict:
    with connection() as conn:
        run = query_one(conn, "SELECT * FROM pipeline_runs WHERE run_id = %s", (run_id,))
        if not run:
            raise HTTPException(404, "run not found")
        stages = query_all(
            conn,
            "SELECT stage, status, started_at, finished_at, info FROM pipeline_stages WHERE run_id = %s",
            (run_id,),
        )
        by_status = query_all(
            conn,
            "SELECT status, count(*) AS n FROM decisions WHERE run_id = %s GROUP BY status",
            (run_id,),
        )
        sends = query_one(conn, "SELECT count(*) AS n FROM sends WHERE run_id = %s", (run_id,))
        funnel = query_one(
            conn,
            """
            SELECT
                count(*)                                            AS candidates,
                count(*) FILTER (WHERE action = 'send')             AS targeted,
                count(*) FILTER (WHERE status = 'dispatched')       AS dispatched,
                count(*) FILTER (WHERE holdout_group = 'control')   AS control,
                count(*) FILTER (WHERE status = 'suppressed' AND holdout_group IS NULL) AS suppressed
            FROM decisions WHERE run_id = %s
            """,
            (run_id,),
        )
    stage_order = {s: i for i, s in enumerate(
        ["profile", "cohort", "strategy", "personalize", "govern", "dispatch", "measure"])}
    stages.sort(key=lambda s: stage_order.get(s["stage"], 99))
    return {
        "run": run,
        "stages": stages,
        "decisions_by_status": {r["status"]: r["n"] for r in by_status},
        "sends": sends["n"] if sends else 0,
        "funnel": funnel or {},
    }


@app.get("/api/runs/{run_id}/cohorts")
def run_cohorts(run_id: str) -> list[dict]:
    with connection() as conn:
        cohorts = query_all(
            conn,
            """
            SELECT c.cohort_id, c.key, c.name, c.description, c.size, c.stats,
                   s.strategy, s.provider, s.model, s.tokens, s.cost_usd
            FROM cohorts c
            LEFT JOIN cohort_strategies s ON s.cohort_id = c.cohort_id
            WHERE c.run_id = %s
            ORDER BY c.size DESC
            """,
            (run_id,),
        )
        counts = query_all(
            conn,
            """
            SELECT cohort_id,
                   count(*) FILTER (WHERE status = 'dispatched')                          AS reached,
                   count(*) FILTER (WHERE holdout_group = 'control')                       AS control,
                   count(*) FILTER (WHERE status = 'suppressed' AND holdout_group IS NULL) AS suppressed
            FROM decisions WHERE run_id = %s GROUP BY cohort_id
            """,
            (run_id,),
        )
    by_cohort = {str(c["cohort_id"]): c for c in counts}
    for c in cohorts:
        cc = by_cohort.get(str(c["cohort_id"]), {})
        c["reached"] = cc.get("reached", 0)
        c["control"] = cc.get("control", 0)
        c["suppressed"] = cc.get("suppressed", 0)
    return cohorts


@app.get("/api/runs/{run_id}/decisions")
def run_decisions(
    run_id: str,
    cohort: str | None = None,
    status: str | None = None,
    limit: int = Query(25, le=200),
) -> list[dict]:
    clauses = ["d.run_id = %s"]
    params: list[Any] = [run_id]
    if cohort:
        clauses.append("c.key = %s")
        params.append(cohort)
    if status:
        clauses.append("d.status = %s")
        params.append(status)
    params.append(limit)
    with connection() as conn:
        return query_all(
            conn,
            f"""
            SELECT d.decision_id, d.customer_id, d.action, d.channel, d.product_id, d.status,
                   d.holdout_group, d.suppressed_reason, d.offer, d.message, d.instruction,
                   c.key AS cohort_key, c.name AS cohort_name, cu.full_name, cat.title AS product_title
            FROM decisions d
            JOIN cohorts c    ON c.cohort_id = d.cohort_id
            JOIN customers cu ON cu.customer_id = d.customer_id
            LEFT JOIN catalog cat ON cat.product_id = d.product_id
            WHERE {' AND '.join(clauses)}
            ORDER BY d.status, d.customer_id
            LIMIT %s
            """,
            tuple(params),
        )


@app.get("/api/runs/{run_id}/suppressions")
def run_suppressions(run_id: str) -> list[dict]:
    with connection() as conn:
        rows = query_all(
            conn,
            """
            SELECT
                CASE WHEN suppressed_reason LIKE 'strategy:%%' THEN 'strategy_stay_quiet'
                     ELSE suppressed_reason END AS reason,
                count(*) AS n
            FROM decisions
            WHERE run_id = %s AND status = 'suppressed'
            GROUP BY 1 ORDER BY n DESC
            """,
            (run_id,),
        )
    return rows


@app.get("/api/runs/{run_id}/measurement")
def run_measurement(run_id: str) -> dict:
    with connection() as conn:
        rows = query_all(
            conn,
            """
            SELECT scope, label, cohort_id, treatment_n, treatment_conv, control_n, control_conv,
                   treatment_rate, control_rate, abs_lift, rel_lift, ci_low, ci_high, p_value, revenue_lift
            FROM measurements WHERE run_id = %s
            ORDER BY scope DESC, treatment_n DESC
            """,
            (run_id,),
        )
    overall = next((r for r in rows if r["scope"] == "overall"), None)
    per_cohort = [r for r in rows if r["scope"] == "cohort"]
    return {"overall": overall, "per_cohort": per_cohort}


@app.get("/api/customers/{customer_id}")
def customer(customer_id: str) -> dict:
    with connection() as conn:
        profile = query_one(conn, "SELECT * FROM customer_profiles WHERE customer_id = %s", (customer_id,))
        if not profile:
            raise HTTPException(404, "customer not found")
        return profile


class RunRequest(BaseModel):
    objective: str | None = None


@app.post("/api/runs")
def trigger_run(req: RunRequest) -> dict:
    settings = get_settings()
    objective = req.objective or settings.default_objective
    result = run_pipeline(objective=objective)
    return {"run_id": result["run_id"], "objective": result["objective"]}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
