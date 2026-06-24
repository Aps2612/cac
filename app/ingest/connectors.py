"""Connector / webhook ingest stubs (Step 1: ingest).

In production these are the data connectors and webhooks that stream a brand's
events into Postgres. Here they are thin, *idempotent* upserts onto the same raw
tables the synthetic generator writes to, so re-delivery of a webhook (which
happens constantly in real life) never corrupts state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg

from app.db import connection


def _ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def upsert_customer(payload: dict, conn: psycopg.Connection | None = None) -> str:
    """Idempotently upsert a customer (identity + consent) from a webhook body."""
    def _run(c: psycopg.Connection) -> str:
        c.execute(
            """
            INSERT INTO customers (customer_id, email, phone, full_name, country, city,
                                   signup_ts, acquisition_source, consent_email, consent_sms,
                                   consent_whatsapp, consent_push, marketing_opt_out, raw)
            VALUES (%(customer_id)s, %(email)s, %(phone)s, %(full_name)s, %(country)s, %(city)s,
                    %(signup_ts)s, %(acquisition_source)s, %(consent_email)s, %(consent_sms)s,
                    %(consent_whatsapp)s, %(consent_push)s, %(marketing_opt_out)s, '{}'::jsonb)
            ON CONFLICT (customer_id) DO UPDATE SET
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                consent_email = EXCLUDED.consent_email,
                consent_sms = EXCLUDED.consent_sms,
                consent_whatsapp = EXCLUDED.consent_whatsapp,
                consent_push = EXCLUDED.consent_push,
                marketing_opt_out = EXCLUDED.marketing_opt_out
            """,
            {
                "customer_id": payload["customer_id"],
                "email": payload.get("email"),
                "phone": payload.get("phone"),
                "full_name": payload.get("full_name"),
                "country": payload.get("country"),
                "city": payload.get("city"),
                "signup_ts": _ts(payload.get("signup_ts")),
                "acquisition_source": payload.get("acquisition_source"),
                "consent_email": payload.get("consent_email", True),
                "consent_sms": payload.get("consent_sms", False),
                "consent_whatsapp": payload.get("consent_whatsapp", False),
                "consent_push": payload.get("consent_push", False),
                "marketing_opt_out": payload.get("marketing_opt_out", False),
            },
        )
        return payload["customer_id"]

    if conn is not None:
        return _run(conn)
    with connection() as c:
        return _run(c)


def ingest_event(payload: dict, conn: psycopg.Connection | None = None) -> str:
    """Idempotently ingest a single behavioral event (web or app)."""
    def _run(c: psycopg.Connection) -> str:
        c.execute(
            """
            INSERT INTO events (event_id, customer_id, event_ts, source, event_type, product_id, session_id)
            VALUES (%(event_id)s, %(customer_id)s, %(event_ts)s, %(source)s, %(event_type)s,
                    %(product_id)s, %(session_id)s)
            ON CONFLICT (event_id) DO NOTHING
            """,
            {
                "event_id": payload["event_id"],
                "customer_id": payload["customer_id"],
                "event_ts": _ts(payload.get("event_ts")),
                "source": payload.get("source", "web"),
                "event_type": payload.get("event_type", "page_view"),
                "product_id": payload.get("product_id"),
                "session_id": payload.get("session_id"),
            },
        )
        return payload["event_id"]

    if conn is not None:
        return _run(conn)
    with connection() as c:
        return _run(c)


def ingest_order(payload: dict, conn: psycopg.Connection | None = None) -> str:
    """Idempotently ingest an order and its line items."""
    def _run(c: psycopg.Connection) -> str:
        c.execute(
            """
            INSERT INTO orders (order_id, customer_id, order_ts, total_amount, item_count,
                                discount_amount, used_discount, channel, status)
            VALUES (%(order_id)s, %(customer_id)s, %(order_ts)s, %(total_amount)s, %(item_count)s,
                    %(discount_amount)s, %(used_discount)s, %(channel)s, %(status)s)
            ON CONFLICT (order_id) DO UPDATE SET
                total_amount = EXCLUDED.total_amount,
                status = EXCLUDED.status
            """,
            {
                "order_id": payload["order_id"],
                "customer_id": payload["customer_id"],
                "order_ts": _ts(payload.get("order_ts")),
                "total_amount": payload.get("total_amount", 0),
                "item_count": payload.get("item_count", len(payload.get("items", []))),
                "discount_amount": payload.get("discount_amount", 0),
                "used_discount": payload.get("used_discount", False),
                "channel": payload.get("channel"),
                "status": payload.get("status", "completed"),
            },
        )
        for item in payload.get("items", []):
            c.execute(
                """
                INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
                VALUES (%(order_item_id)s, %(order_id)s, %(product_id)s, %(quantity)s, %(unit_price)s)
                ON CONFLICT (order_item_id) DO NOTHING
                """,
                {
                    "order_item_id": item["order_item_id"],
                    "order_id": payload["order_id"],
                    "product_id": item["product_id"],
                    "quantity": item.get("quantity", 1),
                    "unit_price": item.get("unit_price", 0),
                },
            )
        return payload["order_id"]

    if conn is not None:
        return _run(conn)
    with connection() as c:
        return _run(c)
