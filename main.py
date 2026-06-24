"""CAC mini - customer decisioning in one file.

The idea: instead of blasting one campaign to everyone, decide for EACH customer
the best next action (an offer on their channel, or stay quiet), then PROVE it
worked by holding out a random control group and measuring the incremental lift.

Pipeline (all in memory, no database):

    generate -> profile (RFM) -> cohort -> strategy -> personalize
             -> govern (consent + holdout) -> simulate outcomes -> measure lift

Run:  python3 main.py          (Python 3.10+, standard library only)
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

# --- knobs -------------------------------------------------------------------
N_CUSTOMERS = 5000
SEED = 7
CONTROL_HOLDOUT = 0.15   # fraction held back as control (never messaged)
MAX_DISCOUNT = 30        # governance cap on any discount percent

CATEGORIES = ["skincare", "coffee", "apparel", "home", "fitness", "beauty"]


# =============================================================================
# 1-2. GENERATE + PROFILE
# A real system ingests orders/events and computes this in SQL. Here we just
# synthesize the finished per-customer profile: Recency, Frequency, Monetary.
# =============================================================================
@dataclass
class Customer:
    cid: str
    recency_days: int       # days since last order   (R)
    order_count: int        # number of orders         (F)
    monetary: float         # total spend              (M)
    top_category: str
    email_open_rate: float
    consent_email: bool
    opted_out: bool


# Latent segments shape a realistic spread. Cohorting never sees these labels;
# it re-derives everything from R/F/M, which keeps the demo honest.
# (weight, order_count range, recency range or None if never bought, spend mult)
_SEGMENTS = [
    (0.12, (4, 9), (1, 25), 1.4),     # champions
    (0.10, (3, 7), (40, 130), 1.7),   # lapsing VIPs
    (0.18, (2, 4), (3, 160), 1.0),    # repeat buyers
    (0.14, (1, 1), (15, 70), 0.9),    # at-risk first-timers
    (0.20, (1, 1), (80, 320), 0.8),   # one-and-done
    (0.10, (1, 3), (200, 500), 1.0),  # dormant
    (0.16, (0, 0), None, 0.0),        # prospects (never bought)
]


def _pick_segment(rng: random.Random):
    r, cum = rng.random(), 0.0
    for seg in _SEGMENTS:
        cum += seg[0]
        if r <= cum:
            return seg
    return _SEGMENTS[-1]


def generate(n: int, seed: int) -> list[Customer]:
    rng = random.Random(seed)
    out: list[Customer] = []
    for i in range(1, n + 1):
        _, orders_rng, rec_rng, mult = _pick_segment(rng)
        order_count = rng.randint(*orders_rng)
        if order_count == 0 or rec_rng is None:
            recency, monetary = 10_000, 0.0          # sentinel: never bought
        else:
            recency = rng.randint(*rec_rng)
            monetary = round(order_count * rng.uniform(30, 90) * mult, 2)
        opted_out = rng.random() < 0.05
        out.append(Customer(
            cid=f"C{i:05d}",
            recency_days=recency,
            order_count=order_count,
            monetary=monetary,
            top_category=rng.choice(CATEGORIES),
            email_open_rate=round(rng.uniform(0.05, 0.6), 2),
            consent_email=(not opted_out) and rng.random() < 0.92,
            opted_out=opted_out,
        ))
    return out


# =============================================================================
# 3. COHORT - the RFM ladder. The first rule that matches wins, so every
# targeted customer lands in exactly one bucket. Only customers with >=1 order
# are relevant to the "reactivate lapsing" objective.
# =============================================================================
def cohort_of(c: Customer, vip_spend: float) -> str | None:
    if c.order_count == 0:
        return None                                  # prospect: not targeted
    if c.order_count >= 3 and c.recency_days <= 30:
        return "loyal_regular"
    if c.monetary >= vip_spend and 31 <= c.recency_days <= 150:
        return "lapsing_vip"
    if c.order_count == 1 and 14 <= c.recency_days <= 75:
        return "at_risk_first_timer"
    if c.order_count == 1 and c.recency_days > 75:
        return "one_and_done"
    if c.order_count >= 2 and 31 <= c.recency_days <= 180:
        return "repeat_winback"
    if c.recency_days > 180:
        return "dormant_winback"
    return "recent_nurture"


# =============================================================================
# 4. STRATEGY per cohort. In the full system an LLM authors this from each
# cohort's stats (one call per cohort = bounded cost). Here it's a simple rule
# table - same idea, zero cost. suppress=True means "stay quiet" (the key
# insight: the best message is sometimes no message).
# =============================================================================
@dataclass
class Strategy:
    suppress: bool
    discount: int
    angle: str


STRATEGY = {
    "loyal_regular":       Strategy(True,  0,  "Stay quiet - happy and recently active"),
    "lapsing_vip":         Strategy(False, 15, "We miss you - a small VIP thank-you"),
    "at_risk_first_timer": Strategy(False, 10, "Hope you love your first order"),
    "one_and_done":        Strategy(False, 20, "See what's new - a reason to come back"),
    "repeat_winback":      Strategy(False, 12, "Time to restock?"),
    "dormant_winback":     Strategy(False, 25, "A lot has changed - take another look"),
    "recent_nurture":      Strategy(False, 0,  "Helpful tips, no discount"),
}

COHORT_ORDER = list(STRATEGY.keys())


# =============================================================================
# 5. PERSONALIZE - resolve the specifics for one customer (here: the offer code).
# =============================================================================
def offer_code(cohort: str, cid: str) -> str:
    suffix = hashlib.sha1(cid.encode()).hexdigest()[:5].upper()
    return f"{cohort[:3].upper()}{suffix}"


# =============================================================================
# 6. GOVERN - never message without consent; randomly hold out a control group
# so the lift we measure later is real and not just noise.
# =============================================================================
def _frac(*parts: str) -> float:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return int(digest[:12], 16) / 0xFFFFFFFFFFFF


def decide_group(c: Customer, strat: Strategy) -> str:
    """Return 'suppressed', 'control', or 'treatment' for one customer."""
    if strat.suppress:
        return "suppressed"
    if c.opted_out or not c.consent_email:
        return "suppressed"
    if strat.discount > MAX_DISCOUNT:
        return "suppressed"
    return "control" if _frac("holdout", c.cid) < CONTROL_HOLDOUT else "treatment"


# =============================================================================
# 7. SIMULATE OUTCOMES - control gets only its base purchase odds; treatment
# gets a lift proportional to how relevant the message is. (Production reads
# real conversions here instead.)
# =============================================================================
def base_prob(c: Customer) -> float:
    p = 0.04 + 0.10 * math.exp(-c.recency_days / 100) + 0.10 * c.email_open_rate
    return max(0.02, min(p, 0.30))


def converts(c: Customer, group: str, strat: Strategy) -> bool:
    p = base_prob(c)
    if group == "treatment":
        relevance = 1.6 + (0.4 if strat.discount > 0 else 0.0)
        p = min(p * relevance, 0.6)
    return _frac("convert", c.cid) < p


# =============================================================================
# 8. MEASURE - incremental lift = treatment rate minus held-out control rate,
# with a two-proportion z-test so we know the lift isn't luck.
# =============================================================================
def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def lift(t_n: int, t_c: int, c_n: int, c_c: int) -> dict:
    tr = t_c / t_n if t_n else 0.0
    cr = c_c / c_n if c_n else 0.0
    abs_lift = tr - cr
    p = 1.0
    if t_n and c_n:
        pool = (t_c + c_c) / (t_n + c_n)
        se = math.sqrt(pool * (1 - pool) * (1 / t_n + 1 / c_n))
        if se > 0:
            p = 2 * (1 - _normal_cdf(abs(abs_lift / se)))
    return {"t_n": t_n, "t_c": t_c, "c_n": c_n, "c_c": c_c,
            "tr": tr, "cr": cr, "abs_lift": abs_lift, "p": p}


# =============================================================================
# Orchestrate the run and print a report.
# =============================================================================
def main() -> None:
    customers = generate(N_CUSTOMERS, SEED)

    buyers = sorted(c.monetary for c in customers if c.order_count > 0)
    vip_spend = buyers[int(0.75 * len(buyers))]      # dynamic 75th-pct VIP bar

    # cohort -> group -> [conversions, n]
    cohorts: dict[str, dict[str, list[int]]] = {}
    targeted = 0
    for c in customers:
        cohort = cohort_of(c, vip_spend)
        if cohort is None:
            continue
        targeted += 1
        strat = STRATEGY[cohort]
        group = decide_group(c, strat)
        stats = cohorts.setdefault(
            cohort, {"treatment": [0, 0], "control": [0, 0], "suppressed": [0, 0]}
        )
        stats[group][1] += 1
        if group in ("treatment", "control") and converts(c, group, strat):
            stats[group][0] += 1

    print("\nCAC mini - objective: reactivate lapsing customers")
    print(f"{len(customers):,} customers | {targeted:,} targeted (>=1 order) "
          f"| VIP bar = ${vip_spend:,.0f}\n")

    print(f"{'cohort':<22}{'size':>6}{'sent':>7}  plan")
    for key in COHORT_ORDER:
        if key not in cohorts:
            continue
        s = cohorts[key]
        size = sum(s[g][1] for g in s)
        plan = "stay quiet" if STRATEGY[key].suppress else f"{STRATEGY[key].discount}% off"
        print(f"{key:<22}{size:>6}{s['treatment'][1]:>7}  {plan}")

    def totals(keys: list[str]) -> dict:
        g = lambda grp, idx: sum(cohorts[k][grp][idx] for k in keys)  # noqa: E731
        return lift(g("treatment", 1), g("treatment", 0), g("control", 1), g("control", 0))

    def row(label: str, m: dict) -> str:
        return (f"{label:<22}{m['tr'] * 100:>6.1f}% {m['cr'] * 100:>6.1f}% "
                f"{m['abs_lift'] * 100:>+6.1f}pp {m['p']:>9.4f}")

    print("\nIncremental lift (treatment vs held-out control):")
    print(f"{'cohort':<22}{'treat':>7} {'ctrl':>6} {'lift':>8} {'p-value':>10}")
    print(row("OVERALL", totals(list(cohorts))))
    for key in COHORT_ORDER:
        if key in cohorts and not STRATEGY[key].suppress and cohorts[key]["treatment"][1]:
            print(row(key, totals([key])))
    print()


if __name__ == "__main__":
    main()
