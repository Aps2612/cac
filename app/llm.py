"""Thin Claude wrapper used only by the three-doors engine (Door 2 + Door 3).

Called to author a *plan* (message + offer) for a new group or a rare VIP — never
per customer. Without ANTHROPIC_API_KEY (or on any error) it reports unavailable
and the caller uses a deterministic rule author instead, so the system always runs.
"""

from __future__ import annotations

import json

from . import config

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[assignment]

_PROMPT = """You are a retention strategist for a skincare brand. Write the messaging plan \
for a {scope}.

Context:
  reason to reach out: {reason}
  buyer type: {buyer_type}
  their main product: {product}
  avg days since last order: {recency}

Encode this hard-won wisdom:
- full_price buyers should get NO discount - a discount just trains them to wait for
  sales. Use a helpful, product-led nudge instead.
- discount_seeker responds to a clear offer; mixed is in between.
- replenishment_due: remind them their product is about to run out.
- gone_quiet: a warm "we miss you". abandoned_cart: nudge them to finish checkout.
- discount is an integer 0-{max_discount}. Keep copy short, warm, no emojis.
  You may use {{product}} as a placeholder in the body.

Respond with ONLY a JSON object:
{{"suppress": bool, "discount": int, "channel_rule": "auto"|"email"|"whatsapp",
  "headline": "<=60 chars", "body": "<=200 chars"}}"""


class LLM:
    def __init__(self) -> None:
        self.model = config.ANTHROPIC_MODEL
        self._client = None
        if config.ANTHROPIC_API_KEY and Anthropic is not None:
            self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    @property
    def available(self) -> bool:
        return self._client is not None

    def plan_for(self, scope: str, ctx: dict) -> dict:
        if self._client is None:
            raise RuntimeError("LLM not configured")
        prompt = _PROMPT.format(scope=scope, max_discount=config.MAX_DISCOUNT, **ctx)
        msg = self._client.messages.create(
            model=self.model, max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
        data = json.loads(text)
        return {
            "suppress": bool(data.get("suppress", False)),
            "discount": max(0, min(int(data.get("discount", 0)), config.MAX_DISCOUNT)),
            "channel_rule": data.get("channel_rule") if data.get("channel_rule")
                            in ("auto", "email", "whatsapp") else "auto",
            "headline": str(data.get("headline", ""))[:120],
            "body": str(data.get("body", ""))[:400],
        }


llm = LLM()
