"""Synthetic e-commerce data generator (Step 1: ingest).

Produces a realistic, deterministic dataset (customers, catalog, orders,
web/app events, channel engagement) and bulk-loads it into the raw tables.

The data is shaped by latent customer *segments* so that, once profiled, the
base naturally splits into the archetype cohorts the decisioning layer targets
(lapsing VIPs, one-and-done buyers, at-risk first-timers, loyal regulars, etc.).
Cohorting never sees these latent labels; it rederives everything from the
profile, keeping the demo honest.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db import connection, copy_rows

CATEGORIES = [
    "skincare",
    "supplements",
    "coffee",
    "apparel",
    "home",
    "fitness",
    "pet",
    "beauty",
]

PRODUCT_NOUNS: dict[str, list[str]] = {
    "skincare": ["Vitamin C Serum", "Night Cream", "Gentle Cleanser", "SPF 50 Sunscreen", "Retinol Oil"],
    "supplements": ["Daily Multivitamin", "Omega-3", "Magnesium Glycinate", "Probiotic", "Creatine"],
    "coffee": ["Single-Origin Beans", "Cold Brew Pack", "Espresso Roast", "Decaf Blend", "Pour-Over Kit"],
    "apparel": ["Merino Tee", "Lounge Joggers", "Rain Shell", "Wool Socks", "Everyday Hoodie"],
    "home": ["Linen Sheets", "Scented Candle", "Ceramic Mug Set", "Throw Blanket", "Reed Diffuser"],
    "fitness": ["Resistance Bands", "Yoga Mat", "Adjustable Dumbbell", "Foam Roller", "Shaker Bottle"],
    "pet": ["Grain-Free Kibble", "Chew Toy", "Calming Treats", "Slow Feeder", "Dental Sticks"],
    "beauty": ["Matte Lipstick", "Volumizing Mascara", "Tinted Balm", "Brow Gel", "Setting Spray"],
}

VARIANTS = ["", " - Travel Size", " - Family Pack", " - Refill", " - Limited Edition", " - Mini"]

PRICE_RANGES: dict[str, tuple[float, float]] = {
    "skincare": (18, 65),
    "supplements": (15, 50),
    "coffee": (12, 40),
    "apparel": (25, 120),
    "home": (20, 95),
    "fitness": (15, 80),
    "pet": (10, 55),
    "beauty": (8, 38),
}

ACQUISITION_SOURCES = ["meta_ads", "google_ads", "organic", "referral", "amazon", "influencer"]


@dataclass
class Segment:
    key: str
    weight: float
    order_count: tuple[int, int]      # inclusive min/max orders
    recency_days: tuple[int, int] | None  # last order age range; None => no orders
    discount_prob: float              # P(an order used a discount)
    engage: float                     # baseline channel-engagement propensity
    app_user_prob: float
    recent_sessions: tuple[int, int]  # sessions in the last 30 days
    aov_mult: float = 1.0             # multiplier on basket size / spend


SEGMENTS: list[Segment] = [
    Segment("champion", 0.12, (4, 9), (1, 22), 0.10, 0.62, 0.80, (6, 18), 1.25),
    Segment("lapsing_vip", 0.10, (3, 7), (45, 115), 0.15, 0.45, 0.55, (0, 2), 1.6),
    Segment("repeat_active", 0.16, (2, 4), (3, 28), 0.30, 0.40, 0.55, (3, 10), 1.0),
    Segment("at_risk_first_timer", 0.12, (1, 1), (20, 55), 0.50, 0.32, 0.45, (1, 5), 0.9),
    Segment("one_and_done", 0.20, (1, 1), (80, 320), 0.72, 0.15, 0.30, (0, 1), 0.85),
    Segment("dormant", 0.10, (1, 3), (210, 520), 0.55, 0.08, 0.25, (0, 1), 1.0),
    Segment("prospect", 0.20, (0, 0), None, 0.0, 0.12, 0.40, (1, 6), 0.0),
]

FIRST_NAMES = ["Aarav", "Diya", "Kabir", "Mira", "Rohan", "Sara", "Liam", "Noah", "Emma", "Olivia",
               "Ava", "Aria", "Vihaan", "Ishaan", "Anaya", "Zoe", "Leo", "Maya", "Arjun", "Nina"]
LAST_NAMES = ["Sharma", "Patel", "Khan", "Reddy", "Nair", "Singh", "Gupta", "Mehta", "Bose", "Iyer",
              "Smith", "Johnson", "Lee", "Garcia", "Brown", "Davis", "Lopez", "Chen", "Kim", "Ali"]
CITIES = [("IN", "Mumbai"), ("IN", "Delhi"), ("IN", "Bengaluru"), ("IN", "Pune"), ("US", "Austin"),
          ("US", "Seattle"), ("US", "Denver"), ("GB", "London"), ("AE", "Dubai"), ("SG", "Singapore")]


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _Buffers:
    customers: list[tuple] = field(default_factory=list)
    catalog: list[tuple] = field(default_factory=list)
    orders: list[tuple] = field(default_factory=list)
    order_items: list[tuple] = field(default_factory=list)
    events: list[tuple] = field(default_factory=list)
    engagement: list[tuple] = field(default_factory=list)


def _build_catalog(rng: random.Random) -> list[dict]:
    products: list[dict] = []
    pidx = 0
    for category in CATEGORIES:
        nouns = PRODUCT_NOUNS[category]
        # ~15 products per category to reach ~120 total
        for i in range(15):
            noun = nouns[i % len(nouns)]
            variant = VARIANTS[(i // len(nouns)) % len(VARIANTS)]
            lo, hi = PRICE_RANGES[category]
            price = round(rng.uniform(lo, hi), 2)
            cost = round(price * rng.uniform(0.4, 0.6), 2)
            pidx += 1
            products.append(
                {
                    "product_id": f"P{pidx:04d}",
                    "title": f"{noun}{variant}",
                    "category": category,
                    "price": price,
                    "cost": cost,
                    "tags": [category, "bestseller"] if i < 3 else [category],
                    "popularity": rng.random(),
                }
            )
    return products


def _pick_segment(rng: random.Random) -> Segment:
    r = rng.random()
    cum = 0.0
    for seg in SEGMENTS:
        cum += seg.weight
        if r <= cum:
            return seg
    return SEGMENTS[-1]


def _gen_orders(
    cust_id: str,
    seg: Segment,
    primary_cat: str,
    products_by_cat: dict[str, list[dict]],
    all_products: list[dict],
    signup_ts: datetime,
    now: datetime,
    rng: random.Random,
    counters: dict,
) -> tuple[list[tuple], list[tuple]]:
    orders: list[tuple] = []
    items: list[tuple] = []
    n_orders = rng.randint(*seg.order_count)
    if n_orders == 0 or seg.recency_days is None:
        return orders, items

    last_age = rng.randint(*seg.recency_days)
    last_order_ts = now - timedelta(days=last_age, hours=rng.randint(0, 23))
    if last_order_ts < signup_ts:
        last_order_ts = signup_ts + timedelta(days=1)

    # Spread earlier orders between signup and the last order.
    order_times = [last_order_ts]
    if n_orders > 1:
        span = (last_order_ts - signup_ts).days or 1
        for _ in range(n_orders - 1):
            d = rng.randint(0, span)
            order_times.append(signup_ts + timedelta(days=d, hours=rng.randint(0, 23)))
    order_times.sort()

    for ots in order_times:
        counters["order"] += 1
        order_id = f"O{counters['order']:08d}"
        n_items = rng.randint(1, 4)
        gross = 0.0
        total_qty = 0
        for _ in range(n_items):
            if rng.random() < 0.7 and products_by_cat.get(primary_cat):
                product = rng.choice(products_by_cat[primary_cat])
            else:
                product = rng.choice(all_products)
            qty = rng.randint(1, 3)
            unit_price = float(product["price"]) * seg.aov_mult
            unit_price = round(unit_price, 2)
            gross += unit_price * qty
            total_qty += qty
            counters["item"] += 1
            items.append((f"OI{counters['item']:09d}", order_id, product["product_id"], qty, unit_price))

        used_discount = rng.random() < seg.discount_prob
        discount_amount = round(gross * rng.uniform(0.1, 0.4), 2) if used_discount else 0.0
        total_amount = round(max(gross - discount_amount, 0.0), 2)
        channel = rng.choice(ACQUISITION_SOURCES)
        orders.append(
            (order_id, cust_id, ots, total_amount, total_qty, discount_amount, used_discount, channel, "completed")
        )
    return orders, items


def _gen_events(
    cust_id: str,
    seg: Segment,
    primary_cat: str,
    products_by_cat: dict[str, list[dict]],
    signup_ts: datetime,
    now: datetime,
    rng: random.Random,
    counters: dict,
) -> list[tuple]:
    events: list[tuple] = []
    is_app = rng.random() < seg.app_user_prob
    cat_products = products_by_cat.get(primary_cat) or []

    def add(ts: datetime, source: str, etype: str, product_id: str | None, session_id: str) -> None:
        counters["event"] += 1
        events.append((f"E{counters['event']:09d}", cust_id, ts, source, etype, product_id, session_id))

    # Recent sessions (drive sessions_30d / product_views_30d).
    n_recent = rng.randint(*seg.recent_sessions)
    for _ in range(n_recent):
        counters["session"] += 1
        session_id = f"S{counters['session']:09d}"
        age_days = rng.randint(0, 29)
        base_ts = now - timedelta(days=age_days, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
        source = "app" if is_app and rng.random() < 0.5 else "web"
        if source == "app":
            add(base_ts, "app", "app_open", None, session_id)
        for step in range(rng.randint(2, 6)):
            ts = base_ts + timedelta(minutes=step * rng.randint(1, 4))
            roll = rng.random()
            if roll < 0.6 and cat_products:
                add(ts, source, "product_view", rng.choice(cat_products)["product_id"], session_id)
            elif roll < 0.78:
                add(ts, source, "page_view", None, session_id)
            elif roll < 0.9 and cat_products:
                add(ts, source, "add_to_cart", rng.choice(cat_products)["product_id"], session_id)
            else:
                add(ts, source, "search", None, session_id)

    # A little older browsing history for tenure realism.
    span_days = max((now - signup_ts).days, 1)
    for _ in range(rng.randint(0, 4)):
        counters["session"] += 1
        session_id = f"S{counters['session']:09d}"
        age = rng.randint(30, span_days) if span_days > 30 else rng.randint(0, span_days)
        ts = now - timedelta(days=age, hours=rng.randint(0, 23))
        pid = rng.choice(cat_products)["product_id"] if cat_products and rng.random() < 0.6 else None
        add(ts, "web", "product_view" if pid else "page_view", pid, session_id)

    return events


def _gen_engagement(
    cust_id: str,
    seg: Segment,
    consents: dict[str, bool],
    signup_ts: datetime,
    now: datetime,
    rng: random.Random,
    counters: dict,
) -> list[tuple]:
    rows: list[tuple] = []
    tenure_days = max((now - signup_ts).days, 1)
    n_messages = min(12, tenure_days // 25 + rng.randint(0, 3))

    # Channels we could have historically sent on (email is the broad default).
    channel_weights = {
        "email": 1.0 if consents["email"] else 0.2,
        "sms": 0.6 if consents["sms"] else 0.0,
        "whatsapp": 0.5 if consents["whatsapp"] else 0.0,
        "push": 0.7 if consents["push"] else 0.0,
    }
    channels = [c for c, w in channel_weights.items() if w > 0]
    weights = [channel_weights[c] for c in channels]
    if not channels:
        return rows

    # Per-customer channel affinity makes one channel clearly preferred.
    affinity = {c: rng.uniform(0.5, 1.5) for c in channels}

    for _ in range(n_messages):
        counters["message"] += 1
        channel = rng.choices(channels, weights=weights, k=1)[0]
        age = rng.randint(1, tenure_days)
        sent_ts = now - timedelta(days=age, hours=rng.randint(0, 23))
        open_p = min(0.95, seg.engage * affinity[channel])
        opened = rng.random() < open_p
        clicked = opened and rng.random() < open_p * 0.55
        rows.append(
            (f"M{counters['message']:09d}", cust_id, channel, sent_ts, True, opened, clicked, "legacy_blast")
        )
    return rows


def generate(n_customers: int, seed: int) -> _Buffers:
    rng = random.Random(seed)
    now = _now()
    buf = _Buffers()

    products = _build_catalog(rng)
    products_by_cat: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    for p in products:
        products_by_cat[p["category"]].append(p)
        buf.catalog.append(
            (p["product_id"], p["title"], p["category"], p["price"], p["cost"], p["tags"], True)
        )

    counters = {"order": 0, "item": 0, "event": 0, "session": 0, "message": 0}

    for idx in range(1, n_customers + 1):
        cust_id = f"C{idx:06d}"
        seg = _pick_segment(rng)
        primary_cat = rng.choice(CATEGORIES)
        country, city = rng.choice(CITIES)
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)

        signup_age = rng.randint(20, 900)
        signup_ts = now - timedelta(days=signup_age, hours=rng.randint(0, 23))

        opt_out = rng.random() < 0.05
        consents = {
            "email": (not opt_out) and rng.random() < 0.92,
            "sms": (not opt_out) and rng.random() < 0.45,
            "whatsapp": (not opt_out) and rng.random() < 0.38,
            "push": (not opt_out) and rng.random() < (0.6 if seg.app_user_prob > 0.4 else 0.25),
        }

        buf.customers.append(
            (
                cust_id,
                f"{first.lower()}.{last.lower()}{idx}@example.com",
                f"+91{rng.randint(7000000000, 9999999999)}",
                f"{first} {last}",
                country,
                city,
                signup_ts,
                rng.choice(ACQUISITION_SOURCES),
                consents["email"],
                consents["sms"],
                consents["whatsapp"],
                consents["push"],
                opt_out,
            )
        )

        orders, items = _gen_orders(
            cust_id, seg, primary_cat, products_by_cat, products, signup_ts, now, rng, counters
        )
        buf.orders.extend(orders)
        buf.order_items.extend(items)
        buf.events.extend(
            _gen_events(cust_id, seg, primary_cat, products_by_cat, signup_ts, now, rng, counters)
        )
        buf.engagement.extend(
            _gen_engagement(cust_id, seg, consents, signup_ts, now, rng, counters)
        )

    return buf


def seed_database(n_customers: int | None = None, seed: int | None = None) -> dict[str, int]:
    """Generate and bulk-load synthetic data. Truncates existing data first."""
    settings = get_settings()
    n_customers = n_customers or settings.synthetic_customers
    seed = seed if seed is not None else settings.synthetic_seed

    buf = generate(n_customers, seed)

    with connection() as conn:
        # CASCADE clears all dependent raw + pipeline data for a clean reseed.
        conn.execute(
            "TRUNCATE customers, catalog, pipeline_runs RESTART IDENTITY CASCADE"
        )
        counts = {
            "customers": copy_rows(
                conn, "customers",
                ["customer_id", "email", "phone", "full_name", "country", "city", "signup_ts",
                 "acquisition_source", "consent_email", "consent_sms", "consent_whatsapp",
                 "consent_push", "marketing_opt_out"],
                buf.customers,
            ),
            "catalog": copy_rows(
                conn, "catalog",
                ["product_id", "title", "category", "price", "cost", "tags", "active"],
                buf.catalog,
            ),
            "orders": copy_rows(
                conn, "orders",
                ["order_id", "customer_id", "order_ts", "total_amount", "item_count",
                 "discount_amount", "used_discount", "channel", "status"],
                buf.orders,
            ),
            "order_items": copy_rows(
                conn, "order_items",
                ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
                buf.order_items,
            ),
            "events": copy_rows(
                conn, "events",
                ["event_id", "customer_id", "event_ts", "source", "event_type", "product_id", "session_id"],
                buf.events,
            ),
            "channel_engagement": copy_rows(
                conn, "channel_engagement",
                ["message_id", "customer_id", "channel", "sent_ts", "delivered", "opened", "clicked", "campaign"],
                buf.engagement,
            ),
        }
    return counts
