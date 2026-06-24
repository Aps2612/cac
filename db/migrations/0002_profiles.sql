-- Per-customer profile: the clean, queryable foundation everything downstream
-- reads. Rebuilt idempotently from the raw layer by db/sql/profile_build.sql.

CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id         text PRIMARY KEY REFERENCES customers(customer_id),
    computed_at         timestamptz NOT NULL DEFAULT now(),
    as_of               timestamptz NOT NULL,

    -- Recency / Frequency / Monetary
    first_order_ts      timestamptz,
    last_order_ts       timestamptz,
    recency_days        integer,
    order_count         integer NOT NULL DEFAULT 0,
    total_spend         numeric(12,2) NOT NULL DEFAULT 0,
    aov                 numeric(12,2) NOT NULL DEFAULT 0,
    frequency_per_year  numeric(10,3) NOT NULL DEFAULT 0,
    monetary            numeric(12,2) NOT NULL DEFAULT 0,

    -- Lifecycle & purchase behavior
    lifecycle_stage     text NOT NULL DEFAULT 'prospect',  -- prospect|new|active|at_risk|lapsed|dormant
    is_repeat           boolean NOT NULL DEFAULT false,
    used_discount_ever  boolean NOT NULL DEFAULT false,
    discount_dependency numeric(5,4) NOT NULL DEFAULT 0,    -- share of orders that used a discount
    top_category        text,
    distinct_categories integer NOT NULL DEFAULT 0,

    -- Behavioral signals
    last_event_ts       timestamptz,
    sessions_30d        integer NOT NULL DEFAULT 0,
    product_views_30d   integer NOT NULL DEFAULT 0,

    -- Channel engagement
    email_send_count    integer NOT NULL DEFAULT 0,
    email_open_rate     numeric(5,4) NOT NULL DEFAULT 0,
    email_click_rate    numeric(5,4) NOT NULL DEFAULT 0,
    sms_click_rate      numeric(5,4) NOT NULL DEFAULT 0,
    push_click_rate     numeric(5,4) NOT NULL DEFAULT 0,
    whatsapp_click_rate numeric(5,4) NOT NULL DEFAULT 0,
    preferred_channel   text,

    -- Consent (denormalized for fast governance checks)
    consent_email       boolean NOT NULL DEFAULT false,
    consent_sms         boolean NOT NULL DEFAULT false,
    consent_whatsapp    boolean NOT NULL DEFAULT false,
    consent_push        boolean NOT NULL DEFAULT false,
    marketing_opt_out   boolean NOT NULL DEFAULT false,

    -- Derived
    predicted_clv       numeric(12,2) NOT NULL DEFAULT 0,
    features            jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_profiles_lifecycle ON customer_profiles(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_profiles_recency ON customer_profiles(recency_days);
CREATE INDEX IF NOT EXISTS idx_profiles_monetary ON customer_profiles(monetary);
