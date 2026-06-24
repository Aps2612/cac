"""Command-line entrypoint: init-db, seed, run, serve, status, webhook-demo."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

import uvicorn

from app.config import get_settings
from app.db import connection, query_all, query_one, run_migrations
from app.ingest.connectors import ingest_event, ingest_order
from app.ingest.synthetic import seed_database
from app.pipeline.run import run_pipeline


def _print(obj: dict) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_init_db(args: argparse.Namespace) -> None:
    applied = run_migrations(reset=args.reset)
    _print({"reset": args.reset, "applied": applied or "already up to date"})


def cmd_seed(args: argparse.Namespace) -> None:
    counts = seed_database(n_customers=args.customers, seed=args.seed)
    _print({"seeded": counts})


def cmd_run(args: argparse.Namespace) -> None:
    result = run_pipeline(objective=args.objective, resume_run_id=args.resume)
    overall = result["stages"].get("measure", {}).get("overall")
    print()
    print(f"Run {result['run_id']} ({result['objective']}) completed.")
    if overall:
        print(
            f"  Lift: treatment {overall['treatment_rate'] * 100:.2f}% vs control "
            f"{overall['control_rate'] * 100:.2f}%  =>  +{overall['abs_lift'] * 100:.2f}pp "
            f"({overall['rel_lift'] * 100:.0f}% relative), p={overall['p_value']}, "
            f"revenue lift ${overall['revenue_lift']:,.0f}"
        )
    print("\nRun `python -m app.cli serve` to explore the result in the dashboard.")


def cmd_status(args: argparse.Namespace) -> None:
    with connection() as conn:
        if args.run:
            run = query_one(conn, "SELECT * FROM pipeline_runs WHERE run_id = %s", (args.run,))
            stages = query_all(
                conn, "SELECT stage, status, info FROM pipeline_stages WHERE run_id = %s ORDER BY started_at", (args.run,)
            )
            _print({"run": run, "stages": stages})
        else:
            runs = query_all(
                conn, "SELECT run_id, objective, status, current_stage, created_at FROM pipeline_runs ORDER BY created_at DESC LIMIT 10"
            )
            _print({"recent_runs": runs})


def cmd_webhook_demo(args: argparse.Namespace) -> None:
    """Show the connector/webhook ingest path: push a live event, then a live order."""
    with connection() as conn:
        cust = query_one(conn, "SELECT customer_id FROM customers ORDER BY customer_id LIMIT 1")
        if not cust:
            print("Seed first: python -m app.cli seed")
            return
        cid = cust["customer_id"]
        product = query_one(conn, "SELECT product_id, price FROM catalog LIMIT 1")
        now = datetime.now(timezone.utc).isoformat()
        ingest_event({"event_id": f"WH-{now}", "customer_id": cid, "event_ts": now,
                      "source": "web", "event_type": "product_view", "product_id": product["product_id"]}, conn)
        ingest_order({"order_id": f"WH-ORD-{now}", "customer_id": cid, "order_ts": now,
                      "total_amount": float(product["price"]), "item_count": 1, "channel": "webhook",
                      "items": [{"order_item_id": f"WH-OI-{now}", "product_id": product["product_id"],
                                 "quantity": 1, "unit_price": float(product["price"])}]}, conn)
        # Idempotency: re-deliver the same order; counts must not change.
        ingest_order({"order_id": f"WH-ORD-{now}", "customer_id": cid, "order_ts": now,
                      "total_amount": float(product["price"]), "item_count": 1, "channel": "webhook",
                      "items": []}, conn)
    _print({"ingested_for_customer": cid, "note": "event + order upserted idempotently via the webhook path"})


def cmd_serve(args: argparse.Namespace) -> None:
    uvicorn.run("app.api.main:app", host=args.host, port=args.port, reload=args.reload)


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    p = argparse.ArgumentParser(prog="cac", description="Customer intelligence / decisioning layer MVP")
    sub = p.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="apply database migrations")
    p_init.add_argument("--reset", action="store_true", help="drop and recreate the schema first")
    p_init.set_defaults(func=cmd_init_db)

    p_seed = sub.add_parser("seed", help="generate + ingest synthetic data")
    p_seed.add_argument("--customers", type=int, default=settings.synthetic_customers)
    p_seed.add_argument("--seed", type=int, default=settings.synthetic_seed)
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="run the full decisioning pipeline")
    p_run.add_argument("--objective", default=settings.default_objective)
    p_run.add_argument("--resume", default=None, help="resume an existing run_id after a crash")
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="show recent runs or a run's stages")
    p_status.add_argument("--run", default=None)
    p_status.set_defaults(func=cmd_status)

    p_wh = sub.add_parser("webhook-demo", help="demonstrate the connector/webhook ingest path")
    p_wh.set_defaults(func=cmd_webhook_demo)

    p_serve = sub.add_parser("serve", help="start the API + dashboard")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8001)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
