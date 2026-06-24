"""Step 5: dispatch.

We do not build sending infrastructure. We emit a validated JSON instruction and
command the channels the brand already has. Here that channel is a mock CEP that
records exactly what would be sent. The send ledger's UNIQUE idempotency key is the
hard guarantee that a re-run (or a crash mid-dispatch) never double-sends.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Jsonb

from app.db import query_all
from app.schemas import Channel, DispatchInstruction, MessageContent, OfferPayload

QUIET_START_HOUR = 8   # inclusive (UTC, for the demo)
QUIET_END_HOUR = 20    # exclusive


def schedule_send_at(now: datetime | None = None) -> datetime:
    """Respect quiet hours: if outside the allowed window, defer to the next 09:00 UTC."""
    now = now or datetime.now(timezone.utc)
    if QUIET_START_HOUR <= now.hour < QUIET_END_HOUR:
        return now
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now.hour >= QUIET_END_HOUR:
        target += timedelta(days=1)
    return target


class MockCEP:
    """Stand-in for Klaviyo / CleverTap / Twilio / own-send channels."""

    provider = "mock_cep"

    def send(self, conn: psycopg.Connection, decision_id: str, run_id: str, instruction: DispatchInstruction) -> dict:
        message_id = "mock-" + hashlib.sha1(instruction.idempotency_key.encode()).hexdigest()[:12]
        inserted = conn.execute(
            """
            INSERT INTO sends (run_id, decision_id, customer_id, channel, idempotency_key,
                               provider, provider_message_id, instruction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING send_id
            """,
            (
                run_id, decision_id, instruction.customer_id, instruction.channel.value,
                instruction.idempotency_key, self.provider, message_id,
                Jsonb(instruction.model_dump(mode="json")),
            ),
        ).fetchone()
        if inserted is None:
            return {"status": "duplicate", "deduped": True, "provider_message_id": message_id}
        return {"status": "sent", "deduped": False, "provider_message_id": message_id}


def _instruction_for(decision: dict, run_id: str, objective: str, send_at: datetime) -> DispatchInstruction:
    msg = decision["message"] or {}
    offer = decision["offer"] or {}
    return DispatchInstruction(
        idempotency_key=f"{run_id}:{decision['customer_id']}:{decision['channel']}",
        run_id=str(run_id),
        decision_id=str(decision["decision_id"]),
        customer_id=decision["customer_id"],
        channel=Channel(decision["channel"]),
        send_at=send_at,
        content=MessageContent(subject=msg.get("subject", ""), body=msg.get("body", ""), cta=msg.get("cta", "")),
        offer=OfferPayload.model_validate(offer) if offer else OfferPayload(),
        metadata={
            "cohort_key": decision["cohort_key"],
            "holdout_group": decision["holdout_group"],
            "objective": objective,
            "to": {"email": decision.get("email"), "phone": decision.get("phone")},
        },
    )


def dispatch_run(conn: psycopg.Connection, run_id: str) -> dict:
    """Dispatch every allowed decision through the mock CEP. Idempotent."""
    run = query_all(conn, "SELECT objective FROM pipeline_runs WHERE run_id = %s", (run_id,))
    objective = run[0]["objective"] if run else ""

    allowed = query_all(
        conn,
        """
        SELECT d.decision_id, d.customer_id, d.channel, d.offer, d.message, d.holdout_group,
               c.key AS cohort_key, cu.email, cu.phone
        FROM decisions d
        JOIN cohorts c    ON c.cohort_id = d.cohort_id
        JOIN customers cu ON cu.customer_id = d.customer_id
        WHERE d.run_id = %s AND d.status = 'allowed'
        """,
        (run_id,),
    )

    cep = MockCEP()
    send_at = schedule_send_at()
    counts = {"dispatched": 0, "deduped": 0}

    for d in allowed:
        instruction = _instruction_for(d, str(run_id), objective, send_at)
        outcome = cep.send(conn, d["decision_id"], str(run_id), instruction)
        if outcome["deduped"]:
            counts["deduped"] += 1
        else:
            counts["dispatched"] += 1
        conn.execute(
            "UPDATE decisions SET status = 'dispatched', instruction = %s, scheduled_for = %s WHERE decision_id = %s",
            (Jsonb(instruction.model_dump(mode="json")), send_at, d["decision_id"]),
        )

    counts["total_allowed"] = len(allowed)
    return counts
