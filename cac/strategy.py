"""Step 4 (strategy): one plan per cohort.

In the full product an LLM authors this from each cohort's stats (one call per
cohort = bounded cost). Here it's a simple, auditable rule table that captures
the same idea -- including the key insight that the best action is sometimes to
*stay quiet* (suppress) rather than fatigue happy customers.

Swapping in a real LLM means replacing this dict with a call that returns the
same ``Strategy`` shape; nothing downstream changes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strategy:
    suppress: bool
    discount: int
    angle: str


STRATEGY: dict[str, Strategy] = {
    "loyal_regular":       Strategy(True,  0,  "Stay quiet - happy and recently active"),
    "lapsing_vip":         Strategy(False, 15, "We miss you - a small VIP thank-you"),
    "at_risk_first_timer": Strategy(False, 10, "Hope you love your first order"),
    "one_and_done":        Strategy(False, 20, "See what's new - a reason to come back"),
    "repeat_winback":      Strategy(False, 12, "Time to restock?"),
    "dormant_winback":     Strategy(False, 25, "A lot has changed - take another look"),
    "recent_nurture":      Strategy(False, 0,  "Helpful tips, no discount"),
}
