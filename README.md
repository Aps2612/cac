# CAC mini

A single-file demo of a customer **decisioning layer**: for every customer, decide the
single best next action — an offer on their channel, or *stay quiet* — then prove it
worked by measuring **incremental lift** against a randomly held-out control group.

## Run

```bash
python3 main.py
```

No dependencies. Python 3.10+ standard library only. Everything lives in `main.py`.

## The pipeline (all in `main.py`)

1. **generate + profile** — synthesize each customer's R/F/M (Recency, Frequency, Monetary).
2. **cohort** — an RFM ladder (first rule that matches wins) puts each buyer in one archetype.
3. **strategy** — a rule per cohort picks the offer, or decides to *stay quiet*.
4. **personalize** — resolve the specifics (the offer code) per customer.
5. **govern** — skip anyone without consent; randomly hold out 15% as a control.
6. **simulate** — control gets base purchase odds; treatment gets a relevance-based uplift.
7. **measure** — compare treatment vs control conversion with a two-proportion z-test.

The output prints each cohort's size and plan, then the incremental lift overall and
per cohort (treatment rate, control rate, lift in percentage points, and a p-value).

> A production version would swap the synthetic data for real event streams, the rule
> table for an LLM call per cohort, and the simulated outcomes for real conversions —
> but the decisioning logic is exactly what's here.
