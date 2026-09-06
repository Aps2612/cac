"""The website's backend: a thin HTTP layer over the seven steps.

    GET  /                -> the dashboard
    GET  /api/health      -> llm status
    GET  /api/state       -> everything the dashboard shows
    GET  /api/spotlight   -> trace one real customer through all 7 steps (Meera-style)
    POST /api/generate    -> STEP 1: create the brand's data   {customers, seed}
    POST /api/run         -> run the full pipeline
    POST /api/reset       -> wipe everything
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import config, db, generate, pipeline
from .llm import llm

_STATIC = Path(__file__).with_name("static")
app = FastAPI(title="CAC — the decisioning brain")
db.init_db()


class GenerateBody(BaseModel):
    customers: int = Field(default=240_000, ge=1, le=5_000_000)
    seed: int = 7


def _rows(conn, sql, args=()) -> list[dict]:
    cur = conn.execute(sql, args)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "llm": "claude" if llm.available else "rule-fallback",
            "model": config.ANTHROPIC_MODEL if llm.available else None}


@app.post("/api/generate")
def api_generate(body: GenerateBody) -> dict:
    return generate.generate(body.customers, body.seed)


@app.post("/api/run")
def api_run() -> dict:
    return pipeline.run()


@app.post("/api/reset")
def api_reset() -> dict:
    db.reset_db()
    return {"ok": True}


@app.get("/api/state")
def api_state() -> dict:
    out: dict = {"counts": db.counts(), "run": None, "params": {}, "overall": None,
                 "reasons": [], "funnel": {}, "doors": {}, "plans": [], "sample": []}
    with db.connect() as conn:
        run = conn.execute("SELECT run_id, params FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
        if run:
            out["run"] = run[0]
            out["params"] = json.loads(run[1] or "{}")
            rid = run[0]
            ov = _rows(conn, "SELECT * FROM measurements WHERE run_id=? AND scope='overall'", (rid,))
            out["overall"] = ov[0] if ov else None
            out["reasons"] = _rows(
                conn, "SELECT * FROM measurements WHERE run_id=? AND scope='reason' "
                "ORDER BY (t_n+c_n) DESC", (rid,))
            out["funnel"] = {r["grp"]: r["n"] for r in _rows(
                conn, "SELECT grp, count(*) n FROM decisions WHERE run_id=? GROUP BY grp", (rid,))}
            out["doors"] = {r["door"]: r["n"] for r in _rows(
                conn, "SELECT door, count(*) n FROM decisions WHERE run_id=? GROUP BY door", (rid,))}
            out["sample"] = _rows(
                conn, "SELECT d.customer_id, c.name, d.reason, d.door, d.grp, d.block_reason, "
                "d.channel, d.discount, d.offer_code, d.converted, d.revenue, d.message "
                "FROM decisions d JOIN customers c ON c.customer_id=d.customer_id "
                "WHERE d.run_id=? ORDER BY (d.grp='treatment') DESC, d.revenue DESC LIMIT 20", (rid,))
        out["plans"] = _rows(
            conn, "SELECT plan_key, scope, reason, buyer_type, suppress, discount, "
            "channel_rule, headline, body, source, reused FROM plans ORDER BY reused DESC LIMIT 40")
    return out


@app.get("/api/spotlight")
def api_spotlight() -> dict:
    """One real customer traced through all 7 steps. Prefers a Meera-like story."""
    with db.connect() as conn:
        run = conn.execute("SELECT run_id FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
        if not run:
            return {"found": False}
        rid = run[0]
        # Prefer: treatment, gone_quiet, full-price, whatsapp -> the Meera archetype.
        pick = conn.execute(
            """SELECT d.customer_id FROM decisions d
               JOIN profiles p ON p.customer_id = d.customer_id
               WHERE d.run_id=? AND d.grp='treatment'
               ORDER BY (d.reason='gone_quiet' AND p.buyer_type='full_price'
                         AND d.channel='whatsapp') DESC,
                        (p.buyer_type='full_price') DESC, d.revenue DESC
               LIMIT 1""", (rid,)).fetchone()
        if not pick:
            return {"found": False}
        cid = pick[0]
        cust = dict(conn.execute("SELECT * FROM customers WHERE customer_id=?", (cid,)).fetchone())
        prof = dict(conn.execute("SELECT * FROM profiles WHERE customer_id=?", (cid,)).fetchone())
        dec = dict(conn.execute(
            "SELECT * FROM decisions WHERE run_id=? AND customer_id=?", (rid, cid)).fetchone())
        orders = _rows(conn, "SELECT days_ago, amount, category FROM orders "
                       "WHERE customer_id=? ORDER BY days_ago LIMIT 6", (cid,))
    return {"found": True, "customer": cust, "profile": prof,
            "decision": dec, "orders": orders}
