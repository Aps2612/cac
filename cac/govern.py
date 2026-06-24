"""Steps 5-6 (personalize + govern).

Personalize: build the customer's offer code. Govern: never message without
consent, reject offers over the business cap, and randomly hold out a control
group so the lift we measure later is real and not just noise.
"""

from __future__ import annotations

import hashlib

from .strategy import Strategy

CONTROL_HOLDOUT = 0.15   # fraction held back as control (never messaged)
MAX_DISCOUNT = 30        # governance cap on any discount percent


def _frac(*parts: str) -> float:
    """Deterministic hash -> float in [0, 1). Stable per customer, no RNG state."""
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return int(digest[:12], 16) / 0xFFFFFFFFFFFF


def offer_code(cohort: str, customer_id: str) -> str:
    suffix = hashlib.sha1(customer_id.encode()).hexdigest()[:5].upper()
    return f"{cohort[:3].upper()}{suffix}"


def assign_group(customer_id: str, strat: Strategy, consent_email: int, opted_out: int) -> str:
    """Return 'suppressed', 'control', or 'treatment' for one customer."""
    if strat.suppress:
        return "suppressed"
    if opted_out or not consent_email:
        return "suppressed"
    if strat.discount > MAX_DISCOUNT:
        return "suppressed"
    return "control" if _frac("holdout", customer_id) < CONTROL_HOLDOUT else "treatment"
