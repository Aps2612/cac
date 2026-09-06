# Architecture

The product is a decision layer over a brand's existing tools: for each customer,
every day, choose the single best action, send it on the brand's own channels, and
measure the extra revenue it caused. This document explains *why* the system is
shaped the way it is.

## Design goals (in priority order)

1. **Simple to read, run, and explain.** One SQLite file, one module per step,
   plain synchronous code. The idea is the product, not the plumbing.
2. **AI cost bounded, not per-customer.** Intelligence is expensive; spend it only
   where it changes the decision.
3. **Honest by construction.** Report *caused* revenue (control group + z-test),
   not correlation. Everything reproducible.
4. **Safe.** The AI proposes; deterministic code disposes, behind hard rules.

## The pipeline

```
generate → profile → triage → doors → send(safety + personalize) → measure
 STEP 1     STEP 2    STEP 3   STEP 4        STEP 5–6                STEP 7
```

Each step is one function that runs one or two **set-based SQL statements** over a
wide `profiles` table (one row per customer, each step fills its own columns).
Set-based means the cost is ~constant per step regardless of headcount — 240k
customers run in ~2 seconds locally.

### STEP 1 — data in (`generate.py`)
Synthesises customers with hidden behavioural segments (champions, lapsing VIPs,
one-and-done, prospects…) plus channel habits and price sensitivity. The pipeline
never sees the hidden segments — it re-derives everything from orders, keeping the
demo honest. In production this module is replaced by the brand's real feed.

### STEP 2 — understand (`profile.py`)
One pass computes RFM (recency, frequency, monetary, top category). A second
derives the human traits the rest of the system reasons about: **lifecycle**
(prospect/active/drifting/gone), **buyer type** (full-price/mixed/discount-seeker),
**preferred channel**, **reorder cycle**, and a **baseline buy probability**.

### STEP 3 — triage (`triage.py`)
Most customers need nothing today. Cheap SQL keeps only those crossing a real
threshold now — a product about to run out, someone gone quiet, an abandoned cart
— which is a few percent of the base. The **safety gate** (consent, not opted out,
under the daily frequency cap) is applied here, *before* any AI cost is spent. This
~98% drop is what makes the economics work.

### STEP 4 — the decision engine / three doors (`doors.py`, `llm.py`)
The core cost-control idea: **think once for a whole group, save the plan, reuse it
free.**

- **Door 1 (reuse):** a saved plan for this (reason × buyer-type) already exists →
  apply it. No AI.
- **Door 2 (new group):** no plan yet → the AI writes one plan for the whole group,
  once → cached in the `plans` table.
- **Door 3 (rare VIP):** a per-person AI decision for a few very high-value
  customers, hard-capped by budget.

Because `plans` **persists across runs**, the first run authors plans and every
later run is almost entirely Door 1. Which door a customer took is simply whether
their plan was authored *this* run. Without an API key, a deterministic rule author
stands in for the LLM so the system always runs.

A plan is a mini-playbook: suppress?, discount, channel rule, headline, body (with
a `{product}` placeholder). The LLM writes good plans because we feed it encoded
retention expertise (e.g. *never discount a full-price buyer*).

### STEP 5–6 — safety then send (`send.py`)
Safety first: full-price buyers are forced to 0 discount; anything invalid is
blocked (plan suppressed, no consented channel, out of stock, discount over cap).
Then the message is personalised (real product + channel the customer reads), a
random **control group** is held back, and the outcome is simulated. All randomness
is `md5(prefix + customer_id)` → reproducible.

### STEP 7 — measure (`measure.py`)
For the shortlist overall and per reason: treatment buy-rate vs control buy-rate =
absolute lift, with a two-proportion z-test p-value. Counts come from SQL; the tiny
statistics are done in Python.

## Data model (one SQLite file)

| Table | Role |
|-------|------|
| `customers`, `orders` | STEP 1 raw data |
| `profiles` | one wide row per customer; STEPS 2–4 fill columns |
| `plans` | the persistent saved-plan cache (survives runs → the feedback loop) |
| `decisions` | one decision per shortlisted customer per run |
| `measurements`, `runs` | the lift scoreboard and run log |

## Observations & decisions

- **Triage is the real lever.** The savings come from dropping ~98% of customers
  before any model runs — not from a cheaper model.
- **The cache is the moat.** Persisting plans turns AI from a per-message cost into
  a one-off authoring cost; STEP 7's results feed back to improve future plans.
- **Full-price protection is a hard rule, not a suggestion.** Discounting a loyal
  full-price buyer trains them to wait for sales — the "no discount for Meera" case
  is encoded so the AI can't override it.
- **Safety is a separate gate.** Keeping validation as deterministic code after the
  decision means the AI never sends anything on its own, and cost caps prevent
  runaway bills.
- **SQLite is a feature here.** Zero setup, one file, trivially reproducible. The
  code is set-based, so a future move to Postgres for true multi-million scale is a
  driver swap, not a redesign.
