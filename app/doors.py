"""STEP 4 — the decision engine: route each shortlisted customer through one door.

To keep AI cost near zero, most work is a cache lookup, not an AI call:

  Door 1  a saved plan for this situation already exists -> apply it, free.
  Door 2  a new group (reason + buyer_type) with no plan yet -> AI writes ONE
          plan for the whole group, once; it's cached and reused forever after.
  Door 3  a rare VIP -> AI reasons about that one person. Tightly capped.

Plans persist across runs, so on later runs almost everyone takes Door 1. Which
door a customer took is simply whether their plan was authored on this run.
"""

from __future__ import annotations

from . import config
from .db import connect
from .llm import llm

# Rule fallback per reason: (base discount, headline, body with {product}).
_RULE = {
    "abandoned_cart":    (10, "You left something behind", "Your {product} is still in your cart - complete checkout whenever you're ready."),
    "replenishment_due": (0,  "Running low on {product}?", "Around now your {product} tends to run out - reorder in a tap."),
    "gone_quiet":        (15, "We've missed you", "Here's what's new in your {product} routine - come take a look."),
}
_BUYER_MULT = {"full_price": 0.0, "mixed": 1.0, "discount_seeker": 1.4}


def _rule_plan(reason: str, buyer_type: str) -> dict:
    disc, headline, body = _RULE.get(reason, (0, "An update for you", "Thanks for being a customer."))
    scaled = 0 if buyer_type == "full_price" else int(round(disc * _BUYER_MULT.get(buyer_type, 1.0)))
    return {"suppress": False, "discount": min(scaled, config.MAX_DISCOUNT),
            "channel_rule": "auto", "headline": headline, "body": body}


def _author(scope, reason, buyer_type, ctx, budget) -> tuple[dict, str]:
    if llm.available and budget[0] > 0:
        try:
            plan = llm.plan_for(scope, {"reason": reason, "buyer_type": buyer_type, **ctx})
            budget[0] -= 1
            return plan, "llm"
        except Exception:
            pass
    return _rule_plan(reason, buyer_type), "rule"


def _save_plan(conn, key, scope, reason, buyer_type, plan, source, run_id) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO plans (plan_key, scope, reason, buyer_type, suppress,
               discount, channel_rule, headline, body, source, created_run)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (key, scope, reason, buyer_type, int(plan["suppress"]), plan["discount"],
         plan["channel_rule"], plan["headline"], plan["body"], source, run_id))


def route(run_id: str) -> dict:
    group_budget, vip_budget = [config.MAX_GROUP_LLM], [config.MAX_VIP_LLM]
    made_group = made_vip = 0

    with connect() as conn:
        # --- Door 3: rare VIPs, per person, capped. Reuse a VIP's saved plan if any. ---
        vips = conn.execute(
            """SELECT customer_id, reason, buyer_type, top_category, recency_days
               FROM profiles WHERE on_shortlist = 1 AND is_vip = 1
               ORDER BY monetary DESC LIMIT ?""", (config.MAX_VIP_LLM,)).fetchall()
        vip_plans = {r[0] for r in conn.execute(
            "SELECT plan_key FROM plans WHERE scope = 'vip'")}
        vip_handled = []
        for cid, reason, buyer_type, product, recency in vips:
            vip_handled.append(cid)
            if f"vip:{cid}" in vip_plans:   # already have a plan for this VIP -> reuse (Door 1)
                continue
            ctx = {"product": product or "your routine", "recency": recency or 0}
            plan, source = _author("single VIP customer", reason, buyer_type, ctx, vip_budget)
            _save_plan(conn, f"vip:{cid}", "vip", reason, buyer_type, plan, source, run_id)
            made_vip += 1

        # --- Door 2: one plan per new (reason, buyer_type) group. ---
        needed = conn.execute(
            """SELECT reason, buyer_type,
                      (SELECT top_category FROM profiles p2
                       WHERE p2.reason = p.reason AND p2.buyer_type = p.buyer_type
                         AND p2.on_shortlist = 1 AND top_category IS NOT NULL LIMIT 1) product,
                      CAST(avg(recency_days) AS INT) recency
               FROM profiles p WHERE on_shortlist = 1 AND reason IS NOT NULL
               GROUP BY reason, buyer_type""").fetchall()
        existing = {r[0] for r in conn.execute(
            "SELECT plan_key FROM plans WHERE scope = 'group'")}
        for reason, buyer_type, product, recency in needed:
            key = f"{reason}:{buyer_type}"
            if key in existing:
                continue
            ctx = {"product": product or "your routine", "recency": recency or 0}
            plan, source = _author("customer group", reason, buyer_type, ctx, group_budget)
            _save_plan(conn, key, "group", reason, buyer_type, plan, source, run_id)
            made_group += 1

        # --- Assign each shortlisted customer their plan + door. ---
        vset = set(vip_handled)
        conn.execute(
            """UPDATE profiles SET plan_key =
                   CASE WHEN customer_id IN (%s) THEN 'vip:' || customer_id
                        ELSE reason || ':' || buyer_type END
               WHERE on_shortlist = 1"""
            % (",".join(str(c) for c in vset) or "NULL"))
        conn.execute(
            """UPDATE profiles SET door = (
                   SELECT CASE WHEN pl.created_run = ?
                               THEN (CASE WHEN pl.scope='vip' THEN 'door3' ELSE 'door2' END)
                               ELSE 'door1' END
                   FROM plans pl WHERE pl.plan_key = profiles.plan_key)
               WHERE on_shortlist = 1""", (run_id,))
        conn.execute(
            """UPDATE plans SET reused = reused + (
                   SELECT count(*) FROM profiles
                   WHERE profiles.plan_key = plans.plan_key AND on_shortlist = 1)""")

        doors = {r[0]: r[1] for r in conn.execute(
            "SELECT door, count(*) FROM profiles WHERE on_shortlist = 1 GROUP BY door")}

    return {"doors": doors, "door2_new_groups": made_group, "door3_vips": made_vip,
            "plans_authored": made_group + made_vip,
            "llm": "claude" if llm.available else "rule"}
