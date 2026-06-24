"""Step 3: LLM strategy per cohort.

The orchestrator studies each cohort's brief (its summary stats) and authors a
validated CohortStrategy. This is where the intelligence lives: the model reasons
at the *cohort* level (one call per cohort = bounded cost) and passes its strategy
downstream so we get tailored strategy without paying to reason per individual.

In mock mode a deterministic strategist plays the same role, so the demo shows
differentiated, sensible strategy (including the decision to *stay quiet*) offline.
"""

from __future__ import annotations

import json

import psycopg
from psycopg.types.json import Jsonb

from app.cohort.select import OBJECTIVES
from app.db import query_all
from app.schemas import Channel, CohortStrategy, OfferLogic, OfferType, SequenceStep
from app.strategy.llm import LLMClient

SYSTEM_PROMPT = (
    "You are a senior retention strategist for a consumer brand. Given a cohort brief, "
    "author the single best strategy to serve the stated objective. Rules: keep discounts "
    "within the cohort's max_discount_pct and avoid training discount dependence; prefer the "
    "channel the cohort actually engages with; keep sequences short (1-3 touches). Critically, "
    "choose to STAY QUIET (should_suppress=true) whenever messaging would fatigue happy, "
    "recently-active customers or erode margin for no incremental gain. Output must satisfy the schema."
)


def _dominant_channel(stats: dict) -> Channel:
    mix = {k: v for k, v in (stats.get("channel_mix") or {}).items() if k != "none"}
    if not mix:
        return Channel.email
    best = max(mix, key=mix.get)
    try:
        return Channel(best)
    except ValueError:
        return Channel.email


def _top_category(stats: dict) -> str:
    cats = stats.get("top_categories") or []
    return cats[0]["category"] if cats else "your favorites"


def mock_strategy(key: str, stats: dict) -> CohortStrategy:
    """Deterministic, archetype-aware strategist used in mock mode."""
    channel = _dominant_channel(stats)
    cat = _top_category(stats)

    if key == "loyal_regular":
        return CohortStrategy(
            cohort_key=key,
            objective_fit=(
                "These customers are loyal and bought within the last month. Messaging a "
                "promo now risks fatigue and needlessly discounts customers who would buy anyway."
            ),
            should_suppress=True,
            suppress_reason="Recently active and loyal; stay quiet to protect margin and trust.",
            recommended_channel=channel,
            tone="appreciative",
            guardrails=["No promotional sends", "Reserve for genuine product/loyalty moments"],
        )

    if key == "lapsing_vip":
        return CohortStrategy(
            cohort_key=key,
            objective_fit="High-LTV customers slipping away; a personal, low-discount nudge protects significant revenue.",
            messaging_angle=f"You're one of our best customers and we noticed it's been a while in {cat}.",
            value_proposition=f"Early access to new {cat} plus a small VIP thank-you.",
            recommended_channel=channel,
            offer=OfferLogic(type=OfferType.percent_off, value=15, max_discount_pct=15, min_order_value=0,
                             justification="Modest; VIPs respond to recognition over deep discounts."),
            sequence=[
                SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Personal 'we miss you' + early access"),
                SequenceStep(step=2, channel=Channel.email, timing_hours_after_prev=72, intent="Reminder with curated picks"),
            ],
            tone="premium",
            guardrails=["Lead with recognition, not discount"],
        )

    if key == "at_risk_first_timer":
        return CohortStrategy(
            cohort_key=key,
            objective_fit="The second purchase is the biggest retention lever; nudge before the first-timer goes cold.",
            messaging_angle=f"Hope you're loving your first {cat} order - here's what pairs well with it.",
            value_proposition="A confidence-building second-purchase nudge with helpful recommendations.",
            recommended_channel=channel,
            offer=OfferLogic(type=OfferType.percent_off, value=10, max_discount_pct=12,
                             justification="Light incentive to convert the critical second purchase."),
            sequence=[SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Second-purchase nudge + recommendations")],
            tone="helpful",
            guardrails=["Educate first, discount second"],
        )

    if key == "one_and_done":
        return CohortStrategy(
            cohort_key=key,
            objective_fit="Acquired once (often on discount) and gone; a clear reason to return can recover otherwise-lost CAC.",
            messaging_angle=f"It's been a while - see what's new in {cat} and why customers come back.",
            value_proposition="A compelling reason to give us a second try.",
            recommended_channel=channel,
            offer=OfferLogic(type=OfferType.percent_off, value=20, max_discount_pct=20,
                             justification="These buyers are discount-sensitive; a clear offer earns the re-trial."),
            sequence=[SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Win-back with social proof + offer")],
            tone="friendly",
            guardrails=["Avoid implying the brand is always-on-sale"],
        )

    if key == "repeat_winback":
        return CohortStrategy(
            cohort_key=key,
            objective_fit="Proven repeat buyers who cooled off; a timely restock/new-arrivals nudge re-establishes cadence.",
            messaging_angle=f"Time to restock your {cat}? Here's what's new since your last order.",
            value_proposition="Restock convenience plus fresh arrivals in their favorite category.",
            recommended_channel=channel,
            offer=OfferLogic(type=OfferType.percent_off, value=12, max_discount_pct=15,
                             justification="Light nudge; these customers already value the product."),
            sequence=[SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Restock + new arrivals")],
            tone="warm",
        )

    if key == "dormant_winback":
        return CohortStrategy(
            cohort_key=key,
            objective_fit="Long dormant; a final, stronger win-back is worth one disciplined attempt before sunsetting contact.",
            messaging_angle=f"A lot has changed in {cat} - here's a reason to take another look.",
            value_proposition="A strong, time-bound reason to reactivate.",
            recommended_channel=channel,
            offer=OfferLogic(type=OfferType.percent_off, value=25, max_discount_pct=25,
                             justification="Deep but bounded; this is a last disciplined reactivation attempt."),
            sequence=[SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Strong, time-bound win-back")],
            tone="bold",
            guardrails=["One attempt only; respect frequency caps"],
        )

    # recent_nurture and any fallback.
    return CohortStrategy(
        cohort_key=key,
        objective_fit="Recent buyers worth a gentle, non-promotional nurture to build the habit.",
        messaging_angle=f"Getting the most out of your {cat} - tips and pairings.",
        value_proposition="Helpful content that deepens the relationship without discounting.",
        recommended_channel=channel,
        offer=OfferLogic(type=OfferType.free_shipping, value=0, max_discount_pct=0,
                         justification="No discount needed; nurture value first."),
        sequence=[SequenceStep(step=1, channel=channel, timing_hours_after_prev=0, intent="Educational nurture")],
        tone="warm",
    )


def _build_user_prompt(objective: str, cohort: dict) -> str:
    spec = OBJECTIVES[objective]
    brief = {
        "objective": spec["label"],
        "objective_detail": spec["description"],
        "cohort_key": cohort["key"],
        "cohort_name": cohort["name"],
        "cohort_description": cohort["description"],
        "stats": cohort["stats"],
    }
    return "Cohort brief:\n" + json.dumps(brief, indent=2, default=str)


def author_strategies(conn: psycopg.Connection, run_id: str, objective: str, client: LLMClient | None = None) -> list[dict]:
    """Author + persist one validated strategy per cohort. Returns summaries."""
    client = client or LLMClient()

    cohorts = query_all(
        conn,
        "SELECT cohort_id, key, name, description, size, stats FROM cohorts WHERE run_id = %s ORDER BY size DESC",
        (run_id,),
    )

    results: list[dict] = []
    for cohort in cohorts:
        result = client.complete_json(
            system=SYSTEM_PROMPT,
            user=_build_user_prompt(objective, cohort),
            schema=CohortStrategy,
            mock_factory=lambda c=cohort: mock_strategy(c["key"], c["stats"]),
        )
        strategy: CohortStrategy = result.data  # type: ignore[assignment]

        conn.execute(
            """
            INSERT INTO cohort_strategies (cohort_id, run_id, strategy, provider, model, tokens, cost_usd)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cohort_id) DO UPDATE SET
                strategy = EXCLUDED.strategy,
                provider = EXCLUDED.provider,
                model = EXCLUDED.model,
                tokens = EXCLUDED.tokens,
                cost_usd = EXCLUDED.cost_usd,
                created_at = now()
            """,
            (
                cohort["cohort_id"], run_id, Jsonb(strategy.model_dump(mode="json")),
                result.provider, result.model, result.tokens, result.cost_usd,
            ),
        )
        results.append({
            "cohort_id": str(cohort["cohort_id"]),
            "key": cohort["key"],
            "should_suppress": strategy.should_suppress,
            "provider": result.provider,
            "used_mock": result.used_mock,
        })

    return results
