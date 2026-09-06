"""All the knobs in one place. Read from the environment; nothing secret hardcoded."""

from __future__ import annotations

import os
from pathlib import Path

# Where the SQLite file lives (one file = the whole database, nothing to install).
DB_PATH = Path(__file__).resolve().parent.parent / "cac.db"

# Claude (optional). Without a key, the AI steps use a deterministic rule author.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

# Business policy (STEP 5 safety + STEP 7 measurement).
CONTROL_HOLDOUT = 0.15        # fraction of the shortlist held back, never messaged
MAX_DISCOUNT = 30             # hard cap on any discount percent
MAX_MESSAGES_PER_DAY = 2      # frequency cap: skip if already contacted this much today
OUT_OF_STOCK_RATE = 0.015     # ~1.5% of picks blocked as out of stock (safety demo)

# Triage (STEP 3): who is a rare VIP -> Door 3.
VIP_PERCENTILE = 0.995

# Three-doors cost caps (STEP 4): how many AI calls one run may make.
MAX_GROUP_LLM = 60            # Door 2: one call per new group plan
MAX_VIP_LLM = 30             # Door 3: one call per rare VIP, tightly capped
