# CAC mini — Project & Dashboard Guide

A customer **decisioning pipeline**: for every customer, decide the best next action
(send an offer, or *stay quiet*), then prove it worked by measuring **incremental lift**
against a randomly held-out control group. One SQLite file, zero dependencies.

## Quick start

```bash
python -m cac.cli serve      # then open http://127.0.0.1:8000
```

In the UI: **Seed → Run** (always that order), then read the results.
CLI equivalents: `seed`, `run`, `show`, `reset`.

## Golden rule: two buttons, in order

- **Seed** — create fake customers + their order history (raw data only).
- **Run** — profile → cohort → strategy → govern → measure → results.
- **Reset** — delete the database (`cac.db`) and start fresh.

Run before Seed = nothing to do. Re-Seeding wipes everything (Run again after).

## What each click does (front to back)

Every click = browser → HTTP request → Python function → DB changes → page redraws.

| Button | Endpoint | Runs | Effect |
|--------|----------|------|--------|
| **Seed data** | `POST /api/seed` | `data.seed()` | Loads customers + orders. Profiles stay 0. |
| **Run pipeline** | `POST /api/run` | `pipeline.run()` | Builds profiles, cohorts, decisions, lift. |
| **Reset** | `POST /api/reset` | `reset_db()` | Deletes `cac.db`. |

`Customers` = how many to create. `Seed` = the **random seed** (same seed → identical data, so results are reproducible).

## What the numbers mean

**Stat boxes:** Customers (people) · Orders (purchases) · Profiles (summarized; `0` until you Run) · Run (latest run id).

**Big lift box — the headline:**
- **lift (`+7.5pp`)** — how much *more* the messaged group bought vs. the held-out group, in percentage points. The impact the program actually **caused**.
- **treatment %** — purchase rate of messaged people (count in parentheses).
- **control %** — purchase rate of held-out people (who got nothing).
- **p-value** — chance the result is just luck. **Lower = better**; `< 0.05` = trustworthy.

**Cohorts table:** Size (group total) · Sent (messaged) · Control (held back) · Suppressed (blocked) · Treat / Ctrl (their buy rates) · Lift · p (confidence for that cohort).

**Decisions table:** Group = `treatment` | `control` | `suppressed` · Discount · Code (coupon) · Converted · Revenue.

## The 7 cohorts (RFM ladder — first match wins)

| Cohort | Roughly means | Plan |
|--------|---------------|------|
| `loyal_regular` | Bought 3+ times, active in last 30 days | **Stay quiet** |
| `lapsing_vip` | Big spender, quiet 1–5 months | 15% off, premium "we miss you" |
| `at_risk_first_timer` | Bought once, 2–11 weeks ago | 10% off, nudge 2nd purchase |
| `one_and_done` | Bought once, 75+ days ago | 20% off, win back |
| `repeat_winback` | Bought 2+ times but cooled off | 12% off, "time to restock?" |
| `dormant_winback` | Silent 6+ months | 25% off, last strong attempt |
| `recent_nurture` | Other recent buyers | No discount, just nurture |

Prospects (0 orders) are skipped — they aren't relevant to the "reactivate" objective.

## Gotchas (and why)

- **Profiles = 0 right after Seed** — normal; profiles are built during **Run**.
- **`loyal_regular` shows 0 sent + "stay quiet"** — the whole point: don't fatigue happy, recent buyers. No one to message means no lift number.
- **High p-value or negative lift on small cohorts** — honest statistical noise; trust the **overall** number, which has the most data.
- **Same seed → same results** — every choice (VIP bar, control group, who converts) is deterministic hashing, so runs are reproducible and auditable.

## Files (one module per pipeline stage)

| File | Stage | Does |
|------|-------|------|
| `cac/db.py` | — | SQLite schema + connection |
| `cac/data.py` | 1. ingest | Generate + load synthetic customers/orders |
| `cac/profile.py` | 2. profile | SQL aggregates orders → per-customer RFM |
| `cac/cohort.py` | 3. cohort | RFM ladder → one archetype each |
| `cac/strategy.py` | 4. strategy | A plan per cohort (an LLM would slot in here) |
| `cac/govern.py` | 5–6. personalize + govern | Offer code, consent check, control holdout |
| `cac/measure.py` | 7–8. simulate + measure | Simulate outcomes, then lift + z-test |
| `cac/pipeline.py` | — | Orchestrates a run, persists results |
| `cac/cli.py` | — | `seed` / `run` / `show` / `reset` / `serve` |
| `cac/web.py` | — | The web dashboard (stdlib `http.server`) |
