-- Step 1 (profile): SQL contextual logic that turns raw event history into a
-- clean, queryable per-customer profile. Idempotent: re-running with the same
-- :as_of recomputes the same rows (UPSERT on customer_id).
--
-- Parameter: %(as_of)s  -- the reference "now" for recency / windows.

INSERT INTO customer_profiles AS p (
    customer_id, as_of,
    first_order_ts, last_order_ts, recency_days, order_count, total_spend, aov,
    frequency_per_year, monetary,
    lifecycle_stage, is_repeat, used_discount_ever, discount_dependency,
    top_category, distinct_categories,
    last_event_ts, sessions_30d, product_views_30d,
    email_send_count, email_open_rate, email_click_rate,
    sms_click_rate, push_click_rate, whatsapp_click_rate, preferred_channel,
    consent_email, consent_sms, consent_whatsapp, consent_push, marketing_opt_out,
    predicted_clv, features
)
WITH order_agg AS (
    SELECT
        customer_id,
        count(*)                              AS order_count,
        sum(total_amount)                     AS total_spend,
        min(order_ts)                         AS first_order_ts,
        max(order_ts)                         AS last_order_ts,
        avg(total_amount)                     AS aov,
        bool_or(used_discount)                AS used_discount_ever,
        avg(used_discount::int::numeric)      AS discount_dependency
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
item_cat AS (
    SELECT o.customer_id, cat.category, sum(oi.quantity) AS qty
    FROM order_items oi
    JOIN orders o    ON o.order_id = oi.order_id
    JOIN catalog cat ON cat.product_id = oi.product_id
    GROUP BY o.customer_id, cat.category
),
top_cat AS (
    SELECT DISTINCT ON (customer_id) customer_id, category AS top_category
    FROM item_cat
    ORDER BY customer_id, qty DESC, category
),
cat_count AS (
    SELECT customer_id, count(*) AS distinct_categories
    FROM item_cat
    GROUP BY customer_id
),
event_agg AS (
    SELECT
        customer_id,
        max(event_ts) AS last_event_ts,
        count(DISTINCT session_id)
            FILTER (WHERE event_ts >= %(as_of)s::timestamptz - interval '30 days') AS sessions_30d,
        count(*)
            FILTER (WHERE event_type = 'product_view'
                    AND event_ts >= %(as_of)s::timestamptz - interval '30 days') AS product_views_30d
    FROM events
    GROUP BY customer_id
),
eng AS (
    SELECT
        customer_id,
        count(*) FILTER (WHERE channel = 'email')                          AS email_send_count,
        avg((opened)::int::numeric)  FILTER (WHERE channel = 'email')      AS email_open_rate,
        avg((clicked)::int::numeric) FILTER (WHERE channel = 'email')      AS email_click_rate,
        avg((clicked)::int::numeric) FILTER (WHERE channel = 'sms')        AS sms_click_rate,
        avg((clicked)::int::numeric) FILTER (WHERE channel = 'push')       AS push_click_rate,
        avg((clicked)::int::numeric) FILTER (WHERE channel = 'whatsapp')   AS whatsapp_click_rate
    FROM channel_engagement
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    %(as_of)s::timestamptz AS as_of,
    oa.first_order_ts,
    oa.last_order_ts,
    date_part('day', %(as_of)s::timestamptz - oa.last_order_ts)::int AS recency_days,
    COALESCE(oa.order_count, 0)                                      AS order_count,
    COALESCE(oa.total_spend, 0)                                      AS total_spend,
    COALESCE(oa.aov, 0)                                              AS aov,
    CASE WHEN oa.order_count IS NULL THEN 0
         ELSE round((oa.order_count * 365.0)
              / GREATEST(date_part('day', %(as_of)s::timestamptz - oa.first_order_ts)::numeric, 30), 3)
    END                                                              AS frequency_per_year,
    COALESCE(oa.total_spend, 0)                                      AS monetary,
    CASE
        WHEN oa.order_count IS NULL OR oa.last_order_ts IS NULL THEN 'prospect'
        WHEN date_part('day', %(as_of)s::timestamptz - oa.last_order_ts) <= 30 AND oa.order_count = 1 THEN 'new'
        WHEN date_part('day', %(as_of)s::timestamptz - oa.last_order_ts) <= 30 THEN 'active'
        WHEN date_part('day', %(as_of)s::timestamptz - oa.last_order_ts) <= 90 THEN 'at_risk'
        WHEN date_part('day', %(as_of)s::timestamptz - oa.last_order_ts) <= 180 THEN 'lapsed'
        ELSE 'dormant'
    END                                                              AS lifecycle_stage,
    COALESCE(oa.order_count, 0) >= 2                                 AS is_repeat,
    COALESCE(oa.used_discount_ever, false)                          AS used_discount_ever,
    COALESCE(oa.discount_dependency, 0)                             AS discount_dependency,
    tc.top_category,
    COALESCE(cc.distinct_categories, 0)                            AS distinct_categories,
    ev.last_event_ts,
    COALESCE(ev.sessions_30d, 0)                                   AS sessions_30d,
    COALESCE(ev.product_views_30d, 0)                              AS product_views_30d,
    COALESCE(eng.email_send_count, 0)                              AS email_send_count,
    COALESCE(eng.email_open_rate, 0)                               AS email_open_rate,
    COALESCE(eng.email_click_rate, 0)                              AS email_click_rate,
    COALESCE(eng.sms_click_rate, 0)                                AS sms_click_rate,
    COALESCE(eng.push_click_rate, 0)                               AS push_click_rate,
    COALESCE(eng.whatsapp_click_rate, 0)                           AS whatsapp_click_rate,
    pref.ch                                                         AS preferred_channel,
    c.consent_email, c.consent_sms, c.consent_whatsapp, c.consent_push, c.marketing_opt_out,
    round(COALESCE(oa.total_spend, 0)
          + COALESCE(oa.aov, 0)
            * CASE WHEN oa.order_count IS NULL THEN 0
                   ELSE (oa.order_count * 365.0)
                        / GREATEST(date_part('day', %(as_of)s::timestamptz - oa.first_order_ts)::numeric, 30)
              END, 2)                                              AS predicted_clv,
    jsonb_build_object(
        'tenure_days', date_part('day', %(as_of)s::timestamptz - c.signup_ts)::int,
        'has_any_consent', (c.consent_email OR c.consent_sms OR c.consent_whatsapp OR c.consent_push)
                            AND NOT c.marketing_opt_out
    )                                                              AS features
FROM customers c
LEFT JOIN order_agg oa ON oa.customer_id = c.customer_id
LEFT JOIN top_cat   tc ON tc.customer_id = c.customer_id
LEFT JOIN cat_count cc ON cc.customer_id = c.customer_id
LEFT JOIN event_agg ev ON ev.customer_id = c.customer_id
LEFT JOIN eng         ON eng.customer_id = c.customer_id
LEFT JOIN LATERAL (
    SELECT v.ch
    FROM (VALUES
        ('email',    CASE WHEN c.consent_email    THEN COALESCE(eng.email_click_rate, 0)    ELSE -1 END),
        ('sms',      CASE WHEN c.consent_sms       THEN COALESCE(eng.sms_click_rate, 0)      ELSE -1 END),
        ('whatsapp', CASE WHEN c.consent_whatsapp  THEN COALESCE(eng.whatsapp_click_rate, 0) ELSE -1 END),
        ('push',     CASE WHEN c.consent_push      THEN COALESCE(eng.push_click_rate, 0)     ELSE -1 END)
    ) AS v(ch, score)
    WHERE v.score >= 0 AND NOT c.marketing_opt_out
    ORDER BY v.score DESC, v.ch
    LIMIT 1
) pref ON true
ON CONFLICT (customer_id) DO UPDATE SET
    computed_at         = now(),
    as_of               = EXCLUDED.as_of,
    first_order_ts      = EXCLUDED.first_order_ts,
    last_order_ts       = EXCLUDED.last_order_ts,
    recency_days        = EXCLUDED.recency_days,
    order_count         = EXCLUDED.order_count,
    total_spend         = EXCLUDED.total_spend,
    aov                 = EXCLUDED.aov,
    frequency_per_year  = EXCLUDED.frequency_per_year,
    monetary            = EXCLUDED.monetary,
    lifecycle_stage     = EXCLUDED.lifecycle_stage,
    is_repeat           = EXCLUDED.is_repeat,
    used_discount_ever  = EXCLUDED.used_discount_ever,
    discount_dependency = EXCLUDED.discount_dependency,
    top_category        = EXCLUDED.top_category,
    distinct_categories = EXCLUDED.distinct_categories,
    last_event_ts       = EXCLUDED.last_event_ts,
    sessions_30d        = EXCLUDED.sessions_30d,
    product_views_30d   = EXCLUDED.product_views_30d,
    email_send_count    = EXCLUDED.email_send_count,
    email_open_rate     = EXCLUDED.email_open_rate,
    email_click_rate    = EXCLUDED.email_click_rate,
    sms_click_rate      = EXCLUDED.sms_click_rate,
    push_click_rate     = EXCLUDED.push_click_rate,
    whatsapp_click_rate = EXCLUDED.whatsapp_click_rate,
    preferred_channel   = EXCLUDED.preferred_channel,
    consent_email       = EXCLUDED.consent_email,
    consent_sms         = EXCLUDED.consent_sms,
    consent_whatsapp    = EXCLUDED.consent_whatsapp,
    consent_push        = EXCLUDED.consent_push,
    marketing_opt_out   = EXCLUDED.marketing_opt_out,
    predicted_clv       = EXCLUDED.predicted_clv,
    features            = EXCLUDED.features;
