# CAC — Architecture & Layering

A small, dependency-free customer-decisioning pipeline. One SQLite file, Python
stdlib only. The architecture answers one question honestly:
**"Did messaging customers actually *cause* more purchases?"**

---

## The layered data architecture

The whole system is organized as **layers**, each one a table in `cac.db`, and
each layer is derived *purely* from the layer below it (bronze → silver → gold).

```
                        ┌─────────────────────────────────────────────┐
                        │                 ENTRY POINTS                  │
                        │   CLI (cac/cli.py)   ≡   Web (cac/web.py)      │
                        │        seed · run · show · reset · serve      │
                        └───────────────┬───────────────┬───────────────┘
                                        │               │
                                  seed()│               │run()
                                        ▼               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 — RAW            (what a brand's systems would stream in)           │
│ ─────────────────────────────────────────────────────────────────────────  │
│   customers (id, signup, email_open_rate, consent, opted_out)              │
│   orders    (id, customer_id → customers, days_ago, amount, category)      │
│   source: cac/data.py  ·  written by: seed()                               │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     │  build_profiles()  (SQL rollup)
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 2 — PROFILE        (one clean RFM row per customer)                   │
│ ─────────────────────────────────────────────────────────────────────────  │
│   customer_profiles (customer_id, recency_days, order_count, monetary,     │
│                      top_category)                                         │
│   source: cac/profile.py                                                   │
│   R = recency · F = order_count · M = monetary                             │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     │  cohort → strategy → govern → simulate
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 3 — DECISION       (one decision per targeted customer, per run)      │
│ ─────────────────────────────────────────────────────────────────────────  │
│   decisions (run_id, customer_id, cohort, holdout_group,                   │
│              discount, offer_code, converted, revenue)                     │
│   built by: cac/pipeline.py  using:                                        │
│     • cohort.py   — RFM ladder, first match wins                           │
│     • strategy.py — offer + message angle per cohort                       │
│     • govern.py   — consent, discount cap, treatment/control holdout       │
│     • measure.py  — converts() simulates the outcome                       │
└───────────────────────────────────┬───────────────────────────────────────┘
                                     │  measure()  (lift + two-proportion z-test)
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 4 — MEASUREMENT    (the lift scoreboard, per run)                     │
│ ─────────────────────────────────────────────────────────────────────────  │
│   measurements (run_id, scope, label, t_n, t_c, c_n, c_c,                  │
│                 treat_rate, ctrl_rate, abs_lift, p_value)                  │
│   source: cac/measure.py                                                   │
│   lift = treatment_rate − control_rate   ·   p_value = is it real?         │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## The pipeline as 8 stages

`run()` (in `cac/pipeline.py`) walks every profiled customer through one chain:

| # | Stage        | Module        | What it does                                              |
|---|--------------|---------------|-----------------------------------------------------------|
| 0 | Ingest       | `data.py`     | Generate + load synthetic customers and orders (`seed`).  |
| 1 | Profile      | `profile.py`  | SQL rolls orders into one RFM row per customer.           |
| 2 | VIP bar      | `cohort.py`   | 75th-percentile spend → adaptive "VIP" threshold.         |
| 3 | Cohort       | `cohort.py`   | Sort into one RFM archetype (first match wins).           |
| 4 | Strategy     | `strategy.py` | Each cohort → fixed discount + message angle.             |
| 5 | Personalize  | `govern.py`   | Build the per-customer offer code.                        |
| 6 | Govern       | `govern.py`   | Drop no-consent/opted-out, cap discount, split T/C.       |
| 7 | Simulate     | `measure.py`  | Model who *would* buy (prod reads real sales here).       |
| 8 | Measure      | `measure.py`  | Lift + p-value per cohort and overall.                    |

---

## Key design principles

- **Layer purity** — each layer is rebuilt only from the one below, so the
  pipeline never "cheats" by reading the synthetic segment labels.
- **One module per stage** — single responsibility; easy to read and test.
- **`run_id` per run** — every run is an immutable, queryable experiment record.
- **Reproducibility by design** — `seed` fixes the data; `govern._frac()` uses
  deterministic SHA-256 hashing (not live RNG) for holdout + conversion, so the
  same input always yields identical, auditable output.
- **Core ≡ interface** — CLI and Web are thin front-ends over the same
  functions; no logic lives in the UI.
- **Honest measurement** — a 15% never-messaged **control** holdout is the
  counterfactual; lift = treatment − control; a two-proportion z-test
  (`p_value`) says whether the lift is real or just noise.

---

## The 7 cohorts (RFM ladder, first match wins)

| Cohort                | Rough meaning                  | Offer                         |
|-----------------------|--------------------------------|-------------------------------|
| `loyal_regular`       | Bought 3+, very recent         | Stay quiet (suppress)         |
| `lapsing_vip`         | High spender, cooling off      | Strong win-back               |
| `at_risk_first_timer` | One order, 14–75 days ago      | Nudge second purchase         |
| `one_and_done`        | One order, long ago            | Re-engage                     |
| `repeat_winback`      | Bought 2+, gone quiet          | "Time to restock?"            |
| `dormant_winback`     | Silent 6+ months               | Last strong attempt           |
| `recent_nurture`      | Other recent buyers            | Nurture, no discount          |

Prospects (0 orders) are skipped — they aren't relevant to a reactivation goal.

---

## The honest scope

- Conversions in stage 7 are **simulated**, so lift *magnitudes* are invented —
  the genuine part is the **method** (holdout → lift → significance).
- Cohort thresholds and offers are **hardcoded heuristics**, not learned.
- Single-file SQLite, single run — a teaching/reference model, not a system
  built for scale or concurrency.

What it *is* good for: a runnable mental model and a reference architecture whose
raw → profile → decision → measure shape mirrors real production pipelines.
