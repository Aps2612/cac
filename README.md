# CAC mini

A small **customer decisioning** pipeline: for every customer, decide the single best
next action — an offer on their channel, or *stay quiet* — then prove it worked by
measuring **incremental lift** against a randomly held-out control group.

Backed by a real database with real SQL (**SQLite**, file-based — nothing to install or
run). No external dependencies.

## Run

```bash
python -m cac.cli seed     # generate + load synthetic customers and orders
python -m cac.cli run      # profile -> cohort -> strategy -> govern -> measure
python -m cac.cli show     # reprint the latest run's cohorts + lift
python -m cac.cli reset    # delete the database
python -m cac.cli serve    # open the minimal web UI at http://127.0.0.1:8000
```

### Web UI

`serve` starts a tiny dashboard (Python's built-in `http.server` — still no
dependencies) where you can seed data, run the pipeline, reset, and read the
per-cohort incremental lift in the browser:

```bash
python -m cac.cli serve            # then open http://127.0.0.1:8000
python -m cac.cli serve --port 9000
```

Poke around the data directly:

```bash
sqlite3 cac.db "SELECT cohort, COUNT(*) FROM decisions GROUP BY cohort ORDER BY 2 DESC;"
```

## Layout — one module per pipeline stage

| File | Stage | What it does |
|------|-------|--------------|
| `cac/db.py` | — | SQLite connection + schema (the tables) |
| `cac/data.py` | 1. ingest | Generate + load synthetic customers and orders |
| `cac/profile.py` | 2. profile | SQL aggregates orders into per-customer RFM |
| `cac/cohort.py` | 3. cohort | RFM ladder (first match wins) → one archetype each |
| `cac/strategy.py` | 4. strategy | A plan per cohort (rule table; an LLM would slot in here) |
| `cac/govern.py` | 5-6. personalize + govern | Offer code, consent check, control holdout |
| `cac/measure.py` | 7-8. simulate + measure | Simulate outcomes, then lift + two-proportion z-test |
| `cac/pipeline.py` | — | Orchestrates a run and persists results |
| `cac/cli.py` | — | `seed` / `run` / `show` / `reset` / `serve` |
| `cac/web.py` | — | Minimal stdlib web UI (dashboard + JSON endpoints) |

## Tests

```bash
python -m pytest
```

Covers the cohort ladder and the lift math (no database required).

## Demo vs. production

A production version would swap the synthetic generator for real event streams, the
rule table in `strategy.py` for an LLM call per cohort, SQLite for Postgres, and the
simulated outcomes for real conversions — but the decisioning logic is exactly what's
here.
