"""CAC mini-plus: a small, SQLite-backed customer decisioning pipeline.

For every customer, decide the best next action (an offer on their channel, or
stay quiet), then prove it worked by measuring incremental lift against a
randomly held-out control group. Real database + real SQL, zero setup.
"""

__version__ = "0.2.0"
