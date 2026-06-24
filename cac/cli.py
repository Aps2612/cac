"""Command-line entrypoint:  python -m cac.cli [seed|run|show|reset]."""

from __future__ import annotations

import argparse

from . import data, pipeline
from .db import connect, reset_db


def cmd_seed(args: argparse.Namespace) -> None:
    counts = data.seed(args.customers, args.seed)
    print(f"seeded: {counts['customers']:,} customers, {counts['orders']:,} orders")


def cmd_run(args: argparse.Namespace) -> None:
    res = pipeline.run()
    o = res["overall"]
    print(f"\nrun {res['run_id']} | {res['targeted']:,} customers targeted")
    print(f"OVERALL: treatment {o['treat_rate'] * 100:.1f}% vs control "
          f"{o['ctrl_rate'] * 100:.1f}%  =>  {o['abs_lift'] * 100:+.1f}pp  (p={o['p_value']:.4f})")
    _show(res["run_id"])


def cmd_show(args: argparse.Namespace) -> None:
    conn = connect()
    row = conn.execute(
        "SELECT run_id FROM measurements ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        print("no runs yet - try: python -m cac.cli run")
        return
    _show(row["run_id"])


def _show(run_id: str) -> None:
    conn = connect()
    print(f"\ncohort sizes (run {run_id}):")
    for r in conn.execute(
        """SELECT cohort, COUNT(*) AS size,
                  SUM(holdout_group = 'treatment') AS sent
           FROM decisions WHERE run_id = ? GROUP BY cohort ORDER BY size DESC""",
        (run_id,),
    ):
        print(f"  {r['cohort']:<22}{r['size']:>6}   sent {r['sent']}")

    print(f"\nincremental lift (run {run_id}):")
    print(f"  {'cohort':<22}{'treat':>7}{'ctrl':>8}{'lift':>9}{'p-value':>10}")
    for r in conn.execute(
        """SELECT label, treat_rate, ctrl_rate, abs_lift, p_value
           FROM measurements WHERE run_id = ? ORDER BY scope DESC, t_n DESC""",
        (run_id,),
    ):
        print(f"  {r['label']:<22}{r['treat_rate'] * 100:>6.1f}%{r['ctrl_rate'] * 100:>7.1f}%"
              f"{r['abs_lift'] * 100:>+7.1f}pp{r['p_value']:>10.4f}")
    conn.close()


def cmd_reset(args: argparse.Namespace) -> None:
    reset_db()
    print("database reset (cac.db removed)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cac", description="Customer decisioning pipeline (mini)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="generate + load synthetic data")
    p_seed.add_argument("--customers", type=int, default=5000)
    p_seed.add_argument("--seed", type=int, default=7)
    p_seed.set_defaults(func=cmd_seed)

    sub.add_parser("run", help="run the decisioning pipeline").set_defaults(func=cmd_run)
    sub.add_parser("show", help="show the latest run's cohorts + lift").set_defaults(func=cmd_show)
    sub.add_parser("reset", help="delete the database").set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
