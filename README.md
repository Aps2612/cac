# CAC — the decisioning brain

A "brain" that sits on top of a skincare brand's existing tools and decides, for
**each customer every day, the single best thing to do** — then proves it drove
real extra revenue.

Modelled on a 50-crore brand with **240,000 customers**. Built to be as simple as
possible: one SQLite file, one small module per step, plain synchronous code.

```
ordinary code — most of the system, basically free
an AI judgment — rare and deliberate, the costly part
a safety check — protects the customer and the brand
```

## Run it

```bash
pip install -r requirements.txt          # fastapi, uvicorn, (optional) anthropic
export ANTHROPIC_API_KEY=sk-...           # optional; without it, a rule author is used
uvicorn app.server:app --reload
```

Open <http://localhost:8000>. In the UI:

1. **Generate brand data** — creates the customers + order history (default 240k).
2. **Run the daily decision** — runs all seven steps and shows the results.

At 240k the whole pipeline runs in ~2 seconds. Nothing to install but Python.

## The seven steps

| # | Step | Module | What it does |
|---|------|--------|--------------|
| 1 | Data in | `generate.py` | The brand's orders / channel habits / price behaviour flow in |
| 2 | Understand | `profile.py` | RFM → lifecycle, buyer type, channel, reorder cycle, base buy-rate |
| 3 | Triage | `triage.py` | Keep only the ~few % with a real reason today; safety gate up front |
| 4 | Decide | `doors.py` + `llm.py` | Route each person through one of three doors (AI is rare, plans reused) |
| 5–6 | Safety + send | `send.py` | Block anything invalid, then personalize and "send" on the right channel |
| 7 | Measure | `measure.py` | Hold back a control group; measure the lift we actually caused |

`pipeline.py` runs steps 2–7 in order; `server.py` is the thin HTTP/website layer.

## The three doors (STEP 4) — why AI cost stays near zero

Each shortlisted customer takes **exactly one** door:

- **Door 1 — reuse (≈ most customers):** a saved plan already fits. Code applies
  it. No AI, instant, free.
- **Door 2 — new group:** a new (reason × buyer-type) with no plan yet. The AI
  writes **one** plan for the whole group, once — then it's cached forever.
- **Door 3 — rare VIP:** the AI reasons about one high-value person. Tightly capped.

Plans persist across runs, so the **first run authors plans and later runs are
almost entirely Door 1**. Cost scales with *situations*, not customers.

## Proving it worked (STEP 7)

A random **control group** (15% of the shortlist) gets nothing. Lift = how much
more the messaged group bought than the control; a two-proportion z-test says
whether that gap is real. All randomness is a deterministic hash of the customer
id, so every run is reproducible and auditable.

## Layout

```
app/
  config.py     all the knobs (policy caps, control size, LLM caps)
  db.py         SQLite connection + schema + reset
  generate.py   STEP 1
  profile.py    STEP 2
  triage.py     STEP 3
  doors.py      STEP 4   (three-doors router + plan cache)
  llm.py        Claude wrapper (optional; rule fallback)
  send.py       STEPS 5–6 (safety + personalize + holdout + simulate)
  measure.py    STEP 7
  pipeline.py   orchestrator
  server.py     FastAPI + website
  static/       the dashboard
```

## Demo vs. production

- **Data & outcomes are simulated** so the whole thing runs offline. Production
  swaps `generate.py` for the brand's real feed and the simulated conversion in
  `send.py` for observed conversions — the rest is unchanged.
- **SQLite** keeps setup at zero and handles 240k comfortably. The code is
  set-based, so moving to Postgres later is a driver change, not a rewrite.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the design rationale and observations.
