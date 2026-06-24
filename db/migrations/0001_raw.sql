-- Raw ingest layer: brand event streams land here exactly as connectors /
-- webhooks deliver them. Nothing downstream writes to these tables.

CREATE TABLE IF NOT EXISTS customers (
    customer_id        text PRIMARY KEY,
    email              text,
    phone              text,
    full_name          text,
    country            text,
    city               text,
    signup_ts          timestamptz NOT NULL,
    acquisition_source text,
    -- per-channel consent / preferences
    consent_email      boolean NOT NULL DEFAULT true,
    consent_sms        boolean NOT NULL DEFAULT false,
    consent_whatsapp   boolean NOT NULL DEFAULT false,
    consent_push       boolean NOT NULL DEFAULT false,
    marketing_opt_out  boolean NOT NULL DEFAULT false,
    raw                jsonb NOT NULL DEFAULT '{}'::jsonb,
    ingested_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS catalog (
    product_id text PRIMARY KEY,
    title      text NOT NULL,
    category   text NOT NULL,
    price      numeric(12,2) NOT NULL,
    cost       numeric(12,2),
    tags       text[] NOT NULL DEFAULT '{}',
    active     boolean NOT NULL DEFAULT true,
    raw        jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_catalog_category ON catalog(category);

CREATE TABLE IF NOT EXISTS orders (
    order_id        text PRIMARY KEY,
    customer_id     text NOT NULL REFERENCES customers(customer_id),
    order_ts        timestamptz NOT NULL,
    total_amount    numeric(12,2) NOT NULL,
    item_count      integer NOT NULL,
    discount_amount numeric(12,2) NOT NULL DEFAULT 0,
    used_discount   boolean NOT NULL DEFAULT false,
    channel         text,
    status          text NOT NULL DEFAULT 'completed',
    raw             jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id, order_ts);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id text PRIMARY KEY,
    order_id      text NOT NULL REFERENCES orders(order_id),
    product_id    text NOT NULL REFERENCES catalog(product_id),
    quantity      integer NOT NULL,
    unit_price    numeric(12,2) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

-- Unified web + app behavioral events.
CREATE TABLE IF NOT EXISTS events (
    event_id    text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES customers(customer_id),
    event_ts    timestamptz NOT NULL,
    source      text NOT NULL,   -- web | app
    event_type  text NOT NULL,   -- page_view | product_view | add_to_cart | search | app_open | ...
    product_id  text REFERENCES catalog(product_id),
    session_id  text,
    raw         jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_events_customer ON events(customer_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

-- Historical channel engagement: what the CEP previously sent and how customers reacted.
CREATE TABLE IF NOT EXISTS channel_engagement (
    message_id  text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES customers(customer_id),
    channel     text NOT NULL,   -- email | sms | whatsapp | push
    sent_ts     timestamptz NOT NULL,
    delivered   boolean NOT NULL DEFAULT true,
    opened      boolean NOT NULL DEFAULT false,
    clicked     boolean NOT NULL DEFAULT false,
    campaign    text,
    raw         jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_engagement_customer ON channel_engagement(customer_id, sent_ts);
CREATE INDEX IF NOT EXISTS idx_engagement_channel ON channel_engagement(channel);
