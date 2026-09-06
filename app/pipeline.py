"""Run one full daily decision — the seven steps, in order.

    profile -> triage -> doors -> send(safety + personalize) -> measure

Plain synchronous code: each step is one function call. Plans authored this run
are cached, so the next run is cheaper (more Door 1). That's the feedback loop.
"""

from __future__ import annotations

import json
import uuid

from . import doors, measure, profile, send, triage
from .db import connect


def run() -> dict:
    run_id = uuid.uuid4().hex[:8]

    profiled = profile.build_profiles()      # STEP 2
    tri = triage.shortlist()                 # STEP 3
    dr = doors.route(run_id)                 # STEP 4
    targeted = send.send(run_id)             # STEPS 5-6
    summary = measure.measure(run_id)        # STEP 7

    params = {"profiled": profiled, **tri, **dr}
    with connect() as conn:
        conn.execute("INSERT INTO runs (run_id, params) VALUES (?, ?)",
                     (run_id, json.dumps(params, default=str)))

    return {"run_id": run_id, "targeted": targeted,
            "overall": summary["overall"], **params}
