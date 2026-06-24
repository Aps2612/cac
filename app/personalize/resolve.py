"""Step 4: personalize per customer.

Under the cohort's strategy, resolve the specifics for each individual: the right
product (from catalog + their category affinity, excluding what they already own),
the right offer (within the strategy's bounds), the right channel (their engaged,
consented channel), and the copy. Product/offer/channel selection is deterministic
(cheap and auditable); message copy is templated from the strategy, with an optional
cost-bounded sample resolved by the LLM.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import psycopg
from psycopg.types.json import Jsonb

from app.config import Settings, get_settings
from app.db import query_all
from app.schemas import Channel, CohortStrategy, OfferPayload, OfferType, PersonalizedMessage
from app.strategy.llm import LLMClient

CONSENT_FIELD = {
    Channel.email: "consent_email",
    Channel.sms: "consent_sms",
    Channel.whatsapp: "consent_whatsapp",
    Channel.push: "consent_push",
}


@dataclass
class PersonalizationContext:
    products_by_cat: dict[str, list[dict]] = field(default_factory=dict)
    global_bestsellers: list[dict] = field(default_factory=list)
    purchased: dict[str, set[str]] = field(default_factory=dict)


def build_context(conn: psycopg.Connection, run_id: str) -> PersonalizationContext:
    products = query_all(
        conn,
        "SELECT product_id, title, category, price, ('bestseller' = ANY(tags)) AS bestseller "
        "FROM catalog WHERE active ORDER BY bestseller DESC, price DESC",
    )
    by_cat: dict[str, list[dict]] = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(p)
    bestsellers = [p for p in products if p["bestseller"]] or products

    rows = query_all(
        conn,
        """
        SELECT o.customer_id, oi.product_id
        FROM cohort_members cm
        JOIN orders o       ON o.customer_id = cm.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE cm.run_id = %s
        """,
        (run_id,),
    )
    purchased: dict[str, set[str]] = {}
    for r in rows:
        purchased.setdefault(r["customer_id"], set()).add(r["product_id"])

    return PersonalizationContext(products_by_cat=by_cat, global_bestsellers=bestsellers, purchased=purchased)


def _first_name(full_name: str | None) -> str:
    if full_name:
        return full_name.split()[0]
    return "there"


def _code_suffix(customer_id: str) -> str:
    digest = hashlib.sha1(customer_id.encode()).hexdigest()
    return str(int(digest[:8], 16))[-5:]


def choose_channel(profile: dict, recommended: Channel) -> Channel:
    if profile.get("marketing_opt_out"):
        return recommended  # not deliverable; governance will suppress on consent
    consented = {ch for ch, fld in CONSENT_FIELD.items() if profile.get(fld)}
    if recommended in consented:
        return recommended
    pref = profile.get("preferred_channel")
    if pref:
        try:
            if Channel(pref) in consented:
                return Channel(pref)
        except ValueError:
            pass
    if consented:
        return sorted(consented, key=lambda c: c.value)[0]
    return recommended


def choose_product(profile: dict, ctx: PersonalizationContext) -> dict | None:
    purchased = ctx.purchased.get(profile["customer_id"], set())
    candidates = ctx.products_by_cat.get(profile.get("top_category") or "", []) or ctx.global_bestsellers
    for p in candidates:
        if p["product_id"] not in purchased:
            return p
    for p in ctx.global_bestsellers:
        if p["product_id"] not in purchased:
            return p
    return candidates[0] if candidates else (ctx.global_bestsellers[0] if ctx.global_bestsellers else None)


def offer_payload(strategy: CohortStrategy, customer_id: str) -> OfferPayload:
    o = strategy.offer
    if o.type == OfferType.none:
        return OfferPayload(type=OfferType.none)
    if o.type == OfferType.free_shipping:
        return OfferPayload(code="FREESHIP", type=o.type, value=0, min_order_value=o.min_order_value)
    code = f"{strategy.cohort_key[:3].upper()}{_code_suffix(customer_id)}"
    return OfferPayload(code=code, type=o.type, value=o.value, min_order_value=o.min_order_value)


def template_message(profile: dict, strategy: CohortStrategy, product: dict | None, offer: OfferPayload) -> PersonalizedMessage:
    name = _first_name(profile.get("full_name"))
    product_title = product["title"] if product else "your favorites"

    if offer.type == OfferType.percent_off:
        offer_line = f"Use code {offer.code} for {int(offer.value)}% off."
    elif offer.type == OfferType.amount_off:
        offer_line = f"Use code {offer.code} for {int(offer.value)} off."
    elif offer.type == OfferType.free_shipping:
        offer_line = "Enjoy free shipping on your next order."
    else:
        offer_line = ""

    subject = (strategy.messaging_angle or strategy.value_proposition or "A little something for you")[:160]
    body = (
        f"Hi {name}, {strategy.value_proposition} "
        f"We thought you might like our {product_title}. {offer_line}"
    ).strip()[:1200]
    cta = "Shop now" if offer.type != OfferType.none else "See what's new"
    return PersonalizedMessage(subject=subject, body=body, cta=cta, reason=strategy.objective_fit[:300])


def personalize(
    conn: psycopg.Connection,
    run_id: str,
    client: LLMClient | None = None,
    settings: Settings | None = None,
) -> dict:
    """Resolve a decision for every cohort member and persist it (idempotent)."""
    settings = settings or get_settings()
    client = client or LLMClient()
    ctx = build_context(conn, run_id)

    strat_rows = query_all(
        conn,
        """
        SELECT s.cohort_id, c.key, s.strategy
        FROM cohort_strategies s
        JOIN cohorts c ON c.cohort_id = s.cohort_id
        WHERE s.run_id = %s
        """,
        (run_id,),
    )
    strategies = {r["cohort_id"]: (r["key"], CohortStrategy.model_validate(r["strategy"])) for r in strat_rows}

    members = query_all(
        conn,
        """
        SELECT cm.cohort_id, cp.*, cu.full_name
        FROM cohort_members cm
        JOIN customer_profiles cp ON cp.customer_id = cm.customer_id
        JOIN customers cu         ON cu.customer_id = cm.customer_id
        WHERE cm.run_id = %s
        """,
        (run_id,),
    )

    llm_copy_budget = settings.personalize_llm_sample
    rows: list[tuple] = []
    counts = {"send": 0, "suppress_strategy": 0}

    for m in members:
        cohort_id = m["cohort_id"]
        key, strategy = strategies[cohort_id]

        if strategy.should_suppress:
            counts["suppress_strategy"] += 1
            rows.append((
                run_id, m["customer_id"], cohort_id, "suppress", None, None, None, None,
                "suppressed", f"strategy: {strategy.suppress_reason or 'stay quiet'}",
            ))
            continue

        channel = choose_channel(m, strategy.recommended_channel)
        product = choose_product(m, ctx)
        offer = offer_payload(strategy, m["customer_id"])
        message = template_message(m, strategy, product, offer)

        # Cost-bounded optional LLM copy (no-op in mock mode / when sample exhausted).
        if llm_copy_budget > 0 and not client.provider == "mock":
            result = client.complete_json(
                system="You write concise, on-brand retention copy. Match the schema.",
                user=(
                    f"Customer first name: {_first_name(m.get('full_name'))}. "
                    f"Strategy angle: {strategy.messaging_angle}. Value prop: {strategy.value_proposition}. "
                    f"Featured product: {product['title'] if product else 'n/a'}. "
                    f"Offer: {offer.model_dump()}. Channel: {channel.value}."
                ),
                schema=PersonalizedMessage,
                mock_factory=lambda: message,
            )
            message = result.data  # type: ignore[assignment]
            llm_copy_budget -= 1

        counts["send"] += 1
        rows.append((
            run_id, m["customer_id"], cohort_id, "send", channel.value,
            product["product_id"] if product else None,
            Jsonb(offer.model_dump(mode="json")), Jsonb(message.model_dump(mode="json")),
            "pending", None,
        ))

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO decisions
                (run_id, customer_id, cohort_id, action, channel, product_id, offer, message, status, suppressed_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, customer_id) DO UPDATE SET
                cohort_id = EXCLUDED.cohort_id,
                action = EXCLUDED.action,
                channel = EXCLUDED.channel,
                product_id = EXCLUDED.product_id,
                offer = EXCLUDED.offer,
                message = EXCLUDED.message,
                status = EXCLUDED.status,
                suppressed_reason = EXCLUDED.suppressed_reason
            """,
            rows,
        )

    counts["total"] = len(rows)
    return counts
