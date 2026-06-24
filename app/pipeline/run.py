"""Crash-safe, idempotent pipeline orchestrator.

Runs the full daily decisioning pipeline for an objective. Every stage records its
status in the `pipeline_stages` ledger and is individually idempotent, so a run can
be safely re-executed or resumed after a crash: completed stages are skipped, and
re-running an unfinished stage produces the same result (UPSERTs + the send ledger's
idempotency key guarantee no double work and no double-send).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings, get_settings
from app.cohort.select import OBJECTIVES, select_and_cohort
from app.db import connection, query_all, query_one, to_jsonb
from app.dispatch.cep_mock import dispatch_run
from app.governance.gates import apply_governance
from app.measurement.lift import measure
from app.measurement.simulate import simulate_outcomes
from app.personalize.resolve import personalize
from app.profile.build import build_profiles, profile_summary
from app.strategy.llm import LLMClient
from app.strategy.orchestrator import author_strategies

logger = logging.getLogger("cac.pipeline")

STAGE_ORDER = ["profile", "cohort", "strategy", "personalize", "govern", "dispatch", "measure"]


@dataclass
class RunContext:
    run_id: str
    objective: str
    as_of: datetime
    settings: Settings
    client: LLMClient


def _set_stage(run_id: str, stage: str, status: str, info: dict | None = None) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO pipeline_stages (run_id, stage, status, started_at, info)
            VALUES (%(run_id)s, %(stage)s, %(status)s, now(), COALESCE(%(info)s, '{}'::jsonb))
            ON CONFLICT (run_id, stage) DO UPDATE SET
                status = EXCLUDED.status,
                started_at = COALESCE(pipeline_stages.started_at, now()),
                finished_at = CASE WHEN EXCLUDED.status IN ('completed', 'failed') THEN now() ELSE pipeline_stages.finished_at END,
                info = COALESCE(%(info)s, pipeline_stages.info)
            """,
            {"run_id": run_id, "stage": stage, "status": status, "info": to_jsonb(info) if info is not None else None},
        )
        if status == "running":
            conn.execute("UPDATE pipeline_runs SET current_stage = %s WHERE run_id = %s", (stage, run_id))


def _run_stage(ctx: RunContext, stage: str) -> dict:
    """Execute a single stage's work inside one transaction and return its info."""
    with connection() as conn:
        if stage == "profile":
            n = build_profiles(conn, ctx.as_of)
            return {"profiles": n, **profile_summary(conn)}
        if stage == "cohort":
            summaries = select_and_cohort(conn, ctx.run_id, ctx.objective)
            return {"cohorts": len(summaries), "members": sum(s["size"] for s in summaries)}
        if stage == "strategy":
            res = author_strategies(conn, ctx.run_id, ctx.objective, ctx.client)
            return {"strategies": len(res), "suppressed_cohorts": sum(1 for r in res if r["should_suppress"])}
        if stage == "personalize":
            return personalize(conn, ctx.run_id, ctx.client, ctx.settings)
        if stage == "govern":
            return apply_governance(conn, ctx.run_id, ctx.settings)
        if stage == "dispatch":
            return dispatch_run(conn, ctx.run_id)
        if stage == "measure":
            sim = simulate_outcomes(conn, ctx.run_id, ctx.settings)
            m = measure(conn, ctx.run_id)
            return {"simulated": sim, "overall": m["overall"]}
        raise ValueError(f"unknown stage {stage}")


def _completed_stages(run_id: str) -> set[str]:
    with connection() as conn:
        rows = query_all(
            conn,
            "SELECT stage FROM pipeline_stages WHERE run_id = %s AND status = 'completed'",
            (run_id,),
        )
    return {r["stage"] for r in rows}


def _ensure_data_present() -> None:
    with connection() as conn:
        row = query_one(conn, "SELECT count(*) AS n FROM customers")
    if not row or row["n"] == 0:
        raise RuntimeError("No customers found. Run `python -m app.cli seed` first.")


def create_run(objective: str, as_of: datetime, settings: Settings) -> str:
    with connection() as conn:
        row = query_one(
            conn,
            "INSERT INTO pipeline_runs (objective, as_of, params) VALUES (%s, %s, %s) RETURNING run_id",
            (objective, as_of, to_jsonb({
                "control_holdout_pct": settings.control_holdout_pct,
                "frequency_cap_per_window": settings.frequency_cap_per_window,
                "frequency_window_days": settings.frequency_window_days,
                "llm_provider": settings.effective_llm_provider,
            })),
        )
        run_id = str(row["run_id"])
        for stage in STAGE_ORDER:
            conn.execute(
                "INSERT INTO pipeline_stages (run_id, stage, status) VALUES (%s, %s, 'pending') "
                "ON CONFLICT (run_id, stage) DO NOTHING",
                (run_id, stage),
            )
    return run_id


def run_pipeline(
    objective: str | None = None,
    as_of: datetime | None = None,
    resume_run_id: str | None = None,
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    objective = objective or settings.default_objective
    if objective not in OBJECTIVES:
        raise ValueError(f"Unknown objective '{objective}'. Known: {list(OBJECTIVES)}")

    _ensure_data_present()

    if resume_run_id:
        run = query_one_run(resume_run_id)
        if run is None:
            raise RuntimeError(f"Run {resume_run_id} not found")
        run_id = resume_run_id
        objective = run["objective"]
        as_of = run["as_of"]
        done = _completed_stages(run_id)
        logger.info("Resuming run %s; completed stages: %s", run_id, sorted(done))
    else:
        as_of = as_of or datetime.now(timezone.utc)
        run_id = create_run(objective, as_of, settings)
        done = set()

    ctx = RunContext(
        run_id=run_id,
        objective=objective,
        as_of=as_of,
        settings=settings,
        client=LLMClient(settings=settings),
    )

    stage_info: dict[str, dict] = {}
    for stage in STAGE_ORDER:
        if stage in done:
            logger.info("[%s] skip (already completed)", stage)
            continue
        _set_stage(run_id, stage, "running")
        try:
            info = _run_stage(ctx, stage)
            _set_stage(run_id, stage, "completed", info)
        except Exception as exc:  # noqa: BLE001
            _set_stage(run_id, stage, "failed", {"error": str(exc)})
            _finalize(run_id, "failed")
            logger.exception("[%s] failed", stage)
            raise
        stage_info[stage] = info
        logger.info("[%s] completed: %s", stage, info)

    _finalize(run_id, "completed", llm_cost=ctx.client.cost.usd, llm_calls=ctx.client.cost.calls)
    return {"run_id": run_id, "objective": objective, "stages": stage_info}


def query_one_run(run_id: str) -> dict | None:
    with connection() as conn:
        return query_one(conn, "SELECT * FROM pipeline_runs WHERE run_id = %s", (run_id,))


def _finalize(run_id: str, status: str, llm_cost: float = 0.0, llm_calls: int = 0) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE pipeline_runs
            SET status = %s,
                finished_at = now(),
                current_stage = NULL,
                stats = stats || %s
            WHERE run_id = %s
            """,
            (status, to_jsonb({"llm_cost_usd": round(llm_cost, 6), "llm_calls": llm_calls}), run_id),
        )
