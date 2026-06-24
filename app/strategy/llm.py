"""LLM client wrapper.

Goals:
- Always return a *validated* Pydantic object (or raise), never raw text.
- Bound cost per run (max calls + max USD).
- Run fully offline via a deterministic mock provider (the default), so the demo
  and tests never require an API key. Callers supply a `mock_factory` that builds
  a sensible object from the same inputs, keeping mock output meaningful.
- Degrade gracefully: if a real provider errors or the budget is exhausted, fall
  back to the mock so a demo run never crashes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Callable, TypeVar

import anthropic
import openai
from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

logger = logging.getLogger("cac.llm")

T = TypeVar("T", bound=BaseModel)

# Rough USD pricing per 1M tokens (input, output). Used only for the cost guardrail.
PRICING: dict[str, tuple[float, float]] = {
    "claude-3-5-sonnet": (3.0, 15.0),
    "claude-3-5-haiku": (0.8, 4.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.5, 10.0),
}
_DEFAULT_PRICE = (1.0, 3.0)


def _price_for(model: str) -> tuple[float, float]:
    for key, price in PRICING.items():
        if key in model:
            return price
    return _DEFAULT_PRICE


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class CostTracker:
    """Per-run budget guardrail."""

    max_calls: int
    max_usd: float
    calls: int = 0
    tokens: int = 0
    usd: float = 0.0

    def has_capacity(self) -> bool:
        return self.calls < self.max_calls and self.usd < self.max_usd

    def charge(self, model: str, tokens_in: int, tokens_out: int) -> float:
        in_price, out_price = _price_for(model)
        cost = (tokens_in / 1_000_000) * in_price + (tokens_out / 1_000_000) * out_price
        self.calls += 1
        self.tokens += tokens_in + tokens_out
        self.usd += cost
        return cost


@dataclass
class LLMResult:
    data: BaseModel
    provider: str
    model: str
    tokens: int
    cost_usd: float
    used_mock: bool


class LLMClient:
    def __init__(self, settings: Settings | None = None, cost: CostTracker | None = None):
        self.settings = settings or get_settings()
        self.provider = self.settings.effective_llm_provider
        self.cost = cost or CostTracker(
            max_calls=self.settings.llm_max_calls_per_run,
            max_usd=self.settings.llm_max_usd_per_run,
        )

    @property
    def model(self) -> str:
        if self.provider == "anthropic":
            return self.settings.anthropic_model
        if self.provider == "openai":
            return self.settings.openai_model
        return "mock"

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        mock_factory: Callable[[], T],
        temperature: float = 0.4,
        max_tokens: int = 1200,
        max_retries: int = 2,
    ) -> LLMResult:
        """Return a validated `schema` instance from the configured provider."""
        if self.provider == "mock" or not self.cost.has_capacity():
            return LLMResult(mock_factory(), "mock", "mock", 0, 0.0, used_mock=True)

        try:
            if self.provider == "anthropic":
                obj, tin, tout = self._anthropic(system, user, schema, temperature, max_tokens, max_retries)
            elif self.provider == "openai":
                obj, tin, tout = self._openai(system, user, schema, temperature, max_tokens, max_retries)
            else:  # pragma: no cover - defensive
                return LLMResult(mock_factory(), "mock", "mock", 0, 0.0, used_mock=True)
        except Exception as exc:  # noqa: BLE001 - never let the pipeline crash on an LLM error
            logger.warning("LLM provider %s failed (%s); falling back to mock", self.provider, exc)
            return LLMResult(mock_factory(), "mock", "mock", 0, 0.0, used_mock=True)

        cost = self.cost.charge(self.model, tin, tout)
        return LLMResult(obj, self.provider, self.model, tin + tout, cost, used_mock=False)

    def _anthropic(self, system, user, schema, temperature, max_tokens, max_retries):
        client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        tool = {
            "name": "emit",
            "description": f"Emit a valid {schema.__name__} object.",
            "input_schema": schema.model_json_schema(),
        }
        messages = [{"role": "user", "content": user}]
        last_err: Exception | None = None
        tin = tout = 0
        for _ in range(max_retries + 1):
            resp = client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                tools=[tool],
                tool_choice={"type": "tool", "name": "emit"},
                messages=messages,
            )
            tin += resp.usage.input_tokens
            tout += resp.usage.output_tokens
            payload = next((b.input for b in resp.content if b.type == "tool_use"), None)
            try:
                return schema.model_validate(payload), tin, tout
            except ValidationError as err:
                last_err = err
                messages += [
                    {"role": "assistant", "content": json.dumps(payload)},
                    {"role": "user", "content": f"That failed validation: {err}. Return corrected JSON."},
                ]
        raise last_err or RuntimeError("anthropic returned no valid tool output")

    def _openai(self, system, user, schema, temperature, max_tokens, max_retries):
        client = openai.OpenAI(api_key=self.settings.openai_api_key)
        schema_hint = json.dumps(schema.model_json_schema())
        sys = f"{system}\n\nReturn ONLY a JSON object matching this JSON Schema:\n{schema_hint}"
        messages = [{"role": "system", "content": sys}, {"role": "user", "content": user}]
        last_err: Exception | None = None
        tin = tout = 0
        for _ in range(max_retries + 1):
            resp = client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=messages,
            )
            if resp.usage:
                tin += resp.usage.prompt_tokens
                tout += resp.usage.completion_tokens
            content = resp.choices[0].message.content or "{}"
            try:
                return schema.model_validate(json.loads(content)), tin, tout
            except (ValidationError, json.JSONDecodeError) as err:
                last_err = err
                messages.append({"role": "user", "content": f"That failed validation: {err}. Return corrected JSON."})
        raise last_err or RuntimeError("openai returned no valid output")
