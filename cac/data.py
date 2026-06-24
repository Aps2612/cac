"""Step 1 (ingest): generate synthetic customers + orders and load them.

Latent segments shape a realistic spread of buying behavior. The pipeline never
sees these labels; it re-derives everything from the orders, which keeps the
demo honest.
"""

from __future__ import annotations

import random

from .db import connect, init_db

CATEGORIES = ["skincare", "coffee", "apparel", "home", "fitness", "beauty"]

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


def seed(n_customers: int = 5000, seed: int = 7) -> dict:
    """Generate and load a fresh dataset. Returns row counts."""
    rng = random.Random(seed)
    customers: list[tuple] = []
    orders: list[tuple] = []
    oid = 0

    for i in range(1, n_customers + 1):
        cid = f"C{i:05d}"
        _, orders_rng, rec_rng, mult = _pick_segment(rng)
        n_orders = rng.randint(*orders_rng)
        opted_out = rng.random() < 0.05
        customers.append((
            cid,
            rng.randint(30, 900),
            round(rng.uniform(0.05, 0.6), 2),
            int((not opted_out) and rng.random() < 0.92),
            int(opted_out),
        ))
        if n_orders and rec_rng:
            last = rng.randint(*rec_rng)            # most-recent order age
            for k in range(n_orders):
                oid += 1
                days = last if k == 0 else rng.randint(last, last + 400)
                orders.append((f"O{oid:07d}", cid, days,
                               round(rng.uniform(30, 90) * mult, 2),
                               rng.choice(CATEGORIES)))

    conn = connect()
    try:
        init_db(conn)
        # Clear in FK-safe order (children before parents) so re-seeding an
        # already-populated DB never trips the customers foreign keys.
        for table in ("decisions", "measurements", "customer_profiles", "orders", "customers"):
            conn.execute(f"DELETE FROM {table}")
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
        conn.commit()
    finally:
        conn.close()
    return {"customers": len(customers), "orders": len(orders)}
