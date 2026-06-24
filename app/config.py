"""Application configuration.

All settings have sane defaults so the demo runs with zero configuration.
Values can be overridden via environment variables or a local .env file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "db" / "migrations"
SQL_DIR = ROOT / "db" / "sql"
STATIC_DIR = ROOT / "app" / "api" / "static"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://cac:cac@localhost:55432/cac"

    # LLM
    llm_provider: str = "mock"  # mock | anthropic | openai
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Cost guardrails (per pipeline run)
    llm_max_calls_per_run: int = 200
    llm_max_usd_per_run: float = 5.0

    # Governance
    control_holdout_pct: float = 0.15
    frequency_cap_per_window: int = 1
    frequency_window_days: int = 3
    governance_max_discount_pct: float = 30.0  # business cap on any percent_off
    suppression_list_pct: float = 0.01         # share of base on the do-not-contact list

    # Personalization
    personalize_llm_sample: int = 0

    # Synthetic data
    synthetic_customers: int = 5000
    synthetic_seed: int = 7

    # Default objective for the daily run
    default_objective: str = "reactivate_lapsing"

    @property
    def effective_llm_provider(self) -> str:
        """Resolve the provider, falling back to mock when no key is present.

        Keeps the promise that the demo always runs, even with LLM_PROVIDER set
        to a real provider but no API key configured.
        """
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            return "mock"
        if self.llm_provider == "openai" and not self.openai_api_key:
            return "mock"
        return self.llm_provider


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
