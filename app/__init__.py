"""CAC — a decisioning "brain" for a skincare brand.

For each customer, every day, decide the single best thing to do — then prove it
drove real extra revenue. Seven simple steps, one module each, mirroring the
product exactly:

    1 generate  the brand's data flows in
    2 profile   build an understanding of each customer
    3 triage    pick who's worth contacting today (~1-3%)
    4 doors     choose the action via three doors (AI is rare, plans are reused)
    5-6 send    safety-check, then personalize + send on the right channel
    7 measure   hold out a control group and measure the lift we caused

Kept deliberately small: SQLite (no server), plain synchronous code, set-based
SQL. Easy to read, easy to run, easy to explain.
"""

__version__ = "2.0.0"
