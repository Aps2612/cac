"""Validated contracts for everything the LLM produces and everything we dispatch.

Validation is non-negotiable: the orchestrator only ever persists/acts on objects
that pass these schemas, and the governance layer enforces business bounds on top.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

# Hard structural ceiling on any percentage discount. Governance enforces a
# (typically lower) business cap on top of this.
MAX_DISCOUNT_PCT_CEILING = 60.0


class Channel(str, Enum):
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    push = "push"


class OfferType(str, Enum):
    none = "none"
    percent_off = "percent_off"
    amount_off = "amount_off"
    free_shipping = "free_shipping"


class OfferLogic(BaseModel):
    type: OfferType = OfferType.none
    value: float = Field(0, ge=0, description="Percent (0-100) for percent_off, or currency amount for amount_off.")
    min_order_value: float | None = Field(None, ge=0)
    max_discount_pct: float = Field(
        20.0, ge=0, le=MAX_DISCOUNT_PCT_CEILING,
        description="The strategist's self-imposed ceiling on the discount for this cohort.",
    )
    justification: str = ""

    @field_validator("value")
    @classmethod
    def _cap_percent(cls, v: float) -> float:
        if v > 100:
            raise ValueError("offer value cannot exceed 100")
        return v

    @model_validator(mode="after")
    def _coherent(self) -> "OfferLogic":
        if self.type == OfferType.percent_off and self.value > MAX_DISCOUNT_PCT_CEILING:
            raise ValueError(f"percent_off above structural ceiling {MAX_DISCOUNT_PCT_CEILING}")
        return self


class SequenceStep(BaseModel):
    step: int = Field(ge=1)
    channel: Channel
    timing_hours_after_prev: int = Field(0, ge=0, le=24 * 30)
    intent: str


class CohortStrategy(BaseModel):
    """The strategy an LLM authors for one cohort. One call per cohort."""

    cohort_key: str
    objective_fit: str = Field(description="Why acting on this cohort serves the objective.")
    should_suppress: bool = Field(default=False, description="True => stay quiet, do not message this cohort.")
    suppress_reason: str | None = None
    messaging_angle: str = ""
    value_proposition: str = ""
    recommended_channel: Channel = Channel.email
    offer: OfferLogic = Field(default_factory=OfferLogic)
    sequence: list[SequenceStep] = Field(default_factory=list)
    tone: str = "warm"
    guardrails: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _suppression_is_coherent(self) -> "CohortStrategy":
        if self.should_suppress:
            # Staying quiet means no offer and no sequence.
            self.offer = OfferLogic()
            self.sequence = []
        elif not self.messaging_angle:
            raise ValueError("a non-suppressed strategy must include a messaging_angle")
        return self


class PersonalizedMessage(BaseModel):
    """Per-customer copy resolved under a cohort strategy."""

    subject: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=1200)
    cta: str = Field(min_length=1, max_length=60)
    reason: str = ""


# --- Dispatch contract (the JSON we emit to the CEP) --------------------------

class MessageContent(BaseModel):
    subject: str
    body: str
    cta: str


class OfferPayload(BaseModel):
    code: str | None = None
    type: OfferType = OfferType.none
    value: float = 0
    min_order_value: float | None = None


class DispatchInstruction(BaseModel):
    """The exact command we hand to the brand's CEP (or own-send channel)."""

    schema_version: str = "1.0"
    idempotency_key: str
    run_id: str
    decision_id: str
    customer_id: str
    channel: Channel
    send_at: datetime
    content: MessageContent
    offer: OfferPayload = Field(default_factory=OfferPayload)
    metadata: dict = Field(default_factory=dict)
