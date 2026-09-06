"""STEPS 5-6 — safety-check the decision, then personalize and send.

STEP 5 (safety): the AI never acts on its own. Hard rules block anything invalid —
plan suppressed, no consented channel, out of stock, discount over the cap (and
full-price buyers are forced to 0, protecting their habit: the "no discount for
Meera" rule).

STEP 6 (send): pick the channel they actually read, fill {product} into the copy,
hold back a random control group (who get nothing), and simulate the outcome.
Production swaps the simulation for real observed conversions.

Reproducible: all randomness is a deterministic hash of the customer id.
"""

from __future__ import annotations

import hashlib

from . import config
from .db import connect


def _frac(prefix: str, customer_id: int) -> float:
    """Deterministic float in [0,1) from a hash of prefix + id (stable per customer)."""
    h = hashlib.md5(f"{prefix}:{customer_id}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


_SQL = """
INSERT INTO decisions
    (run_id, customer_id, reason, door, plan_key, grp, block_reason,
     channel, discount, message, offer_code, converted, revenue)
WITH base AS (
    SELECT p.customer_id, p.reason, p.door, p.plan_key, p.buyer_type,
           COALESCE(p.top_category, 'your routine') AS product,
           p.base_prob, p.monetary, p.order_count, p.channel AS pref_channel,
           pl.suppress, pl.discount AS plan_discount, pl.channel_rule, pl.headline, pl.body,
           c.consent_email, c.consent_whatsapp,
           frac('holdout', p.customer_id) AS f_hold,
           frac('convert', p.customer_id) AS f_conv,
           frac('stock',   p.customer_id) AS f_stock
    FROM profiles p
    JOIN customers c ON c.customer_id = p.customer_id
    JOIN plans pl    ON pl.plan_key   = p.plan_key
    WHERE p.on_shortlist = 1
),
chan AS (
    SELECT base.*,
        CASE WHEN buyer_type = 'full_price' THEN 0
             ELSE min(plan_discount, :max) END AS eff_discount,
        CASE
            WHEN channel_rule = 'email'    AND consent_email = 1    THEN 'email'
            WHEN channel_rule = 'whatsapp' AND consent_whatsapp = 1 THEN 'whatsapp'
            WHEN channel_rule = 'auto' AND pref_channel = 'whatsapp' AND consent_whatsapp = 1 THEN 'whatsapp'
            WHEN channel_rule = 'auto' AND pref_channel = 'email'    AND consent_email = 1    THEN 'email'
            WHEN consent_whatsapp = 1 THEN 'whatsapp'
            WHEN consent_email = 1    THEN 'email'
            ELSE NULL END AS channel
    FROM base
),
safe AS (
    SELECT chan.*,
        CASE
            WHEN suppress = 1        THEN 'plan_suppressed'
            WHEN channel IS NULL     THEN 'no_consented_channel'
            WHEN f_stock < :oos      THEN 'out_of_stock'
            WHEN eff_discount > :max THEN 'discount_over_cap'
            ELSE NULL END AS block_reason
    FROM chan
),
decided AS (
    SELECT safe.*,
        CASE WHEN block_reason IS NOT NULL THEN 'blocked'
             WHEN f_hold < :hold THEN 'control' ELSE 'treatment' END AS grp
    FROM safe
),
outcome AS (
    SELECT decided.*,
        CASE
            WHEN grp = 'treatment'
                THEN (f_conv < min(0.60, base_prob * (CASE WHEN eff_discount > 0 THEN 2.0 ELSE 1.6 END)))
            WHEN grp = 'control' THEN (f_conv < base_prob)
            ELSE 0 END AS converted
    FROM decided
)
SELECT :run, customer_id, reason, door, plan_key, grp, block_reason,
    CASE WHEN block_reason IS NULL THEN channel END,
    CASE WHEN block_reason IS NULL THEN eff_discount ELSE 0 END,
    CASE WHEN block_reason IS NULL
         THEN replace(headline, '{product}', product) || ' - ' || replace(body, '{product}', product)
         END,
    CASE WHEN block_reason IS NULL AND grp = 'treatment' AND eff_discount > 0
         THEN 'CAC-' || customer_id END,
    converted,
    CASE WHEN converted = 1 THEN max(monetary / max(order_count, 1), 0) ELSE 0 END
FROM outcome;
"""


def send(run_id: str) -> int:
    with connect() as conn:
        conn.create_function("frac", 2, _frac, deterministic=True)
        conn.execute("DELETE FROM decisions WHERE run_id = ?", (run_id,))
        conn.execute(_SQL, {"run": run_id, "max": config.MAX_DISCOUNT,
                            "oos": config.OUT_OF_STOCK_RATE, "hold": config.CONTROL_HOLDOUT})
        return conn.execute(
            "SELECT count(*) FROM decisions WHERE run_id = ?", (run_id,)).fetchone()[0]
