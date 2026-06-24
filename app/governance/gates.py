"""Governance and safety layer (non-negotiable correctness).

Nothing reaches a channel without passing every gate here. Each gate is a small,
pure, independently testable function; `apply_governance` composes them over a run
and persists the outcome (allowed, or suppressed-with-reason) so every decision is
auditable. We never silently drop a customer.

Gate order (intentional):
  1. consent          - may we contact them on this channel at all?
  2. validation       - is the decision well-formed and within business bounds?
  3. suppression_list - are they on the do-not-contact list?
  4. frequency_cap    - have they been contacted too recently (any system)?
  5. holdout          - among everyone we *would* send to, randomly hold out a
                        control group so we can measure true incremental lift.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import psycopg

from app.config import Settings, get_settings
from app.schemas import Channel, OfferType

CONSENT_FIELD = {
    "email": "consent_email",
    "sms": "consent_sms",
    "whatsapp": "consent_whatsapp",
    "push": "consent_push",
}


# --- Pure, unit-testable gate primitives -------------------------------------

def check_consent(channel: str, consent: dict) -> tuple[bool, str | None]:
    if consent.get("marketing_opt_out"):
        return False, "opted_out"
    field = CONSENT_FIELD.get(channel)
    if field is None:
        return False, "unknown_channel"
    if not consent.get(field):
        return False, "no_consent"
    return True, None


def validate_offer(offer: dict | None, max_discount_pct: float) -> tuple[bool, str | None]:
    if not offer:
        return True, None
    otype = offer.get("type", OfferType.none.value)
    value = float(offer.get("value", 0) or 0)
    if otype == OfferType.percent_off.value and value > max_discount_pct:
        return False, "offer_exceeds_cap"
    if value < 0:
        return False, "invalid_offer"
    return True, None


def _hash_fraction(*parts: str) -> float:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return int(digest[:12], 16) / 0xFFFFFFFFFFFF


def on_suppression_list(customer_id: str, rate: float) -> bool:
    """Deterministic stand-in for an unsubscribe / complaint do-not-contact list."""
    return _hash_fraction("suppress", customer_id) < rate


def assign_holdout(run_id: str, customer_id: str, control_pct: float) -> str:
    """Stable per-run treatment/control assignment."""
    return "control" if _hash_fraction(run_id, customer_id) < control_pct else "treatment"


def frequency_exceeded(recent_contacts: int, cap: int) -> bool:
    return recent_contacts >= cap


# --- DB-aware application over a run -----------------------------------------

@dataclass
class GovernanceResult:
    allowed: int = 0
    control: int = 0
    suppressed: dict[str, int] | None = None

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "control": self.control, "suppressed": self.suppressed or {}}


def _recent_contacts(conn: psycopg.Connection, window_days: int) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT customer_id, count(*) AS n FROM (
            SELECT customer_id FROM channel_engagement
            WHERE sent_ts >= now() - make_interval(days => %(win)s)
            UNION ALL
            SELECT customer_id FROM sends
            WHERE dispatched_at >= now() - make_interval(days => %(win)s)
        ) x GROUP BY customer_id
        """,
        {"win": window_days},
    ).fetchall()
    return {r["customer_id"]: r["n"] for r in rows}


def apply_governance(conn: psycopg.Connection, run_id: str, settings: Settings | None = None) -> dict:
    """Gate every pending send decision for the run; persist allow / suppress outcomes."""
    settings = settings or get_settings()
    recent = _recent_contacts(conn, settings.frequency_window_days)

    pending = conn.execute(
        """
        SELECT d.decision_id, d.customer_id, d.channel, d.offer,
               cp.consent_email, cp.consent_sms, cp.consent_whatsapp, cp.consent_push, cp.marketing_opt_out
        FROM decisions d
        JOIN customer_profiles cp ON cp.customer_id = d.customer_id
        WHERE d.run_id = %s AND d.status = 'pending'
        """,
        (run_id,),
    ).fetchall()

    result = GovernanceResult(suppressed={})
    updates: list[tuple] = []

    for d in pending:
        consent = {
            "marketing_opt_out": d["marketing_opt_out"],
            "consent_email": d["consent_email"],
            "consent_sms": d["consent_sms"],
            "consent_whatsapp": d["consent_whatsapp"],
            "consent_push": d["consent_push"],
        }

        ok, reason = check_consent(d["channel"], consent)
        if ok:
            ok, reason = validate_offer(d["offer"], settings.governance_max_discount_pct)
        if ok and on_suppression_list(d["customer_id"], settings.suppression_list_pct):
            ok, reason = False, "suppression_list"
        if ok and frequency_exceeded(recent.get(d["customer_id"], 0), settings.frequency_cap_per_window):
            ok, reason = False, "frequency_cap"

        if not ok:
            result.suppressed[reason] = result.suppressed.get(reason, 0) + 1
            updates.append(("suppressed", None, reason, d["decision_id"]))
            continue

        group = assign_holdout(str(run_id), d["customer_id"], settings.control_holdout_pct)
        if group == "control":
            result.control += 1
            updates.append(("suppressed", "control", "holdout_control", d["decision_id"]))
        else:
            result.allowed += 1
            updates.append(("allowed", "treatment", None, d["decision_id"]))

    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE decisions SET status = %s, holdout_group = %s, suppressed_reason = %s WHERE decision_id = %s",
            updates,
        )

    return result.to_dict()
