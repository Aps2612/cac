# CAC — Customer Intelligence / Decisioning Layer (MVP)

> The missing brain for customer retention. Instead of one marketer blasting a single
> campaign to 500,000 people, this layer decides, for **every** customer, the single best
> next action: *what to say, when, on which channel, or whether to stay quiet* — then
> commands the brand's existing channels to execute it.

This repository is a self-contained, end-to-end **demo** of that decisioning layer. It runs
the full 5-step pipeline on synthetic e-commerce data, simulates dispatch through a mock CEP
(no real sends), and proves **incremental lift** against a holdout — all visualized in a
dashboard.

## The pipeline

1. **Ingest & profile** — event streams (orders, web/app events, catalog, channel engagement)
   land in Postgres; SQL contextual logic turns raw history into a clean per-customer profile.
2. **Select & cohort (daily)** — for a given objective, select only the relevant customers and
   group them into archetype cohorts.
3. **LLM strategy per cohort** — an LLM orchestrator authors a validated strategy per cohort
   (angle, sequence, offer logic, channel, or "stay quiet"). One call per cohort = bounded cost.
4. **Personalize per customer** — resolve the specific product, offer, channel, and copy for
   each individual under their cohort's strategy.
5. **Dispatch** — emit the final decision as a JSON instruction to a (mock) CEP.

A **governance & safety** layer gates every send (consent, frequency caps, holdouts,
validation). A **measurement** layer uses control groups to prove real incremental lift.

```
ingest -> profile -> cohort -> strategy(LLM) -> personalize -> govern -> dispatch -> measure
```

## Quickstart (3 commands)

Prereqs: Python 3.11+, Docker (for Postgres).

```bash
make install     # create .venv and install the package
make demo        # start Postgres, migrate, seed synthetic data, run the pipeline
make serve       # open the dashboard at http://localhost:8000
```

`make demo` is shorthand for `db-up + init-db + seed + run`. Re-running any step is safe — the
pipeline is idempotent and never double-sends.

### Without Docker

Point `DATABASE_URL` at any reachable Postgres 16 instance (see `.env.example`), then run
`make init-db && make seed && make run`.

## LLM providers

By default `LLM_PROVIDER=mock`: a deterministic, offline strategist so the demo always runs
with no API key. To use a real model, set in `.env`:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

If a real provider is selected but no key is present, the app automatically falls back to the
mock provider. Cost is bounded per run via `LLM_MAX_CALLS_PER_RUN` and `LLM_MAX_USD_PER_RUN`,
and the LLM only reasons at the **cohort** level (a handful of calls), never per customer.

## CLI

```bash
python -m app.cli init-db [--reset]   # apply migrations (optionally drop + recreate)
python -m app.cli seed                # generate + ingest synthetic data
python -m app.cli run [--objective reactivate_lapsing] [--resume RUN_ID]
python -m app.cli serve [--port 8000] # API + dashboard
python -m app.cli webhook-demo        # show the connector/webhook ingest path
```

## Layout

- `db/migrations/*.sql` — schema (raw events, profiles, pipeline ledger, measurement).
- `db/sql/*.sql` — the SQL contextual logic (profile build, cohort selection).
- `app/ingest/` — synthetic generator + connector/webhook stubs.
- `app/profile/`, `app/cohort/` — profiling and cohorting.
- `app/strategy/` — LLM client wrapper (`llm.py`) + cohort orchestrator.
- `app/personalize/` — per-customer resolution.
- `app/governance/` — the non-negotiable safety gates.
- `app/dispatch/` — JSON instruction contract + mock CEP + idempotent send ledger.
- `app/measurement/` — holdout simulation + incremental lift.
- `app/pipeline/` — crash-safe orchestrator + run ledger.
- `app/api/` — FastAPI + the dashboard (zero-build React + Tailwind SPA).
- `tests/` — governance, idempotency, profiling, and schema tests.

## Tests

```bash
make test
```

Governance, idempotency, lift math, and schema-validation tests run without a database. The
profiling and idempotency-against-DB tests are skipped automatically if no Postgres is
reachable.

## Notes on the demo vs. production

- **Dispatch is simulated.** The mock CEP records the exact JSON instruction we would send.
  A real adapter (Klaviyo, Twilio/WhatsApp, email) is a drop-in replacement behind the same
  contract.
- **Outcomes are simulated** by a deterministic response model so lift is reproducible. In
  production the measurement layer reads real conversions.
- The dashboard is a zero-build single-page app (React + Tailwind via CDN) served by FastAPI,
  so the demo runs with only Python — no `npm` required.
