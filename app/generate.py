"""STEP 1 — the brand's existing data flows in.

We synthesise a realistic customer base (orders, channel habits, price behaviour)
so the whole system has something to work on. Hidden behavioural segments shape
the data; the pipeline never sees them — it re-derives everything from orders,
which keeps the demo honest.
"""

from __future__ import annotations

import random

from .db import connect

CATEGORIES = ["vitamin-C serum", "cleanser", "moisturiser", "sunscreen", "toner", "retinol"]

_FIRST = ["Meera", "Aarav", "Isha", "Rohan", "Diya", "Kabir", "Ananya", "Vivaan",
          "Sara", "Arjun", "Nisha", "Dev", "Priya", "Aditya", "Riya", "Karan",
          "Tara", "Neil", "Zoya", "Ishaan", "Maya", "Veer", "Anika", "Yash"]
_LAST = ["S.", "K.", "M.", "R.", "P.", "N.", "V.", "G.", "B.", "D."]

# (weight, order_count range, recency range or None, spend mult, price-sensitivity center)
_SEGMENTS = [
    (0.12, (4, 9), (1, 25), 1.4, 0.30),     # champions (full-price)
    (0.10, (3, 7), (40, 130), 1.7, 0.25),   # lapsing VIPs
    (0.18, (2, 4), (3, 160), 1.0, 0.50),    # repeat buyers
    (0.14, (1, 1), (15, 70), 0.9, 0.60),    # at-risk first-timers
    (0.20, (1, 1), (80, 320), 0.8, 0.70),   # one-and-done
    (0.10, (1, 3), (200, 500), 1.0, 0.55),  # dormant
    (0.16, (0, 0), None, 0.0, 0.50),        # prospects
]


def _pick(rng):
    r, cum = rng.random(), 0.0
    for seg in _SEGMENTS:
        cum += seg[0]
        if r <= cum:
            return seg
    return _SEGMENTS[-1]


def generate(n_customers: int, seed: int = 7) -> dict:
    """Generate n customers (+ their orders) and load them. Returns row counts."""
    rng = random.Random(seed)
    customers, orders = [], []
    oid = 0

    for cid in range(1, n_customers + 1):
        _, orders_rng, rec_rng, mult, price_center = _pick(rng)
        n_orders = rng.randint(*orders_rng)
        opted_out = rng.random() < 0.05
        name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
        customers.append((
            cid, name,
            rng.randint(30, 900),
            round(rng.uniform(0.02, 0.5), 3),                    # email_open_rate
            round(rng.uniform(0.2, 0.9), 3),                     # whatsapp_open_rate
            round(min(1.0, max(0.0, rng.normalvariate(price_center, 0.15))), 3),
            0 if opted_out else int(rng.random() < 0.90),        # consent_email
            0 if opted_out else int(rng.random() < 0.75),        # consent_whatsapp
            int(opted_out),
            0 if opted_out else int(rng.random() < 0.012),       # abandoned_cart
            0 if rng.random() < 0.88 else (1 if rng.random() < 0.8 else 2),  # messages_today
        ))
        if n_orders and rec_rng:
            last = rng.randint(*rec_rng)
            for k in range(n_orders):
                oid += 1
                days = last if k == 0 else rng.randint(last, last + 400)
                orders.append((oid, cid, days,
                               round(rng.uniform(30, 90) * mult, 2),
                               rng.choice(CATEGORIES)))

    with connect() as conn:
        for t in ("measurements", "decisions", "plans", "profiles", "orders", "customers", "runs"):
            conn.execute(f"DELETE FROM {t}")
        conn.executemany(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?)", customers)
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)

    return {"customers": len(customers), "orders": len(orders)}
