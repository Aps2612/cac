-- Step 2 (select + cohort) for objective: reactivate_lapsing.
--
-- We never reason over the whole base: we select only the customers who matter
-- for the objective (people who have purchased at least once) and assign each to
-- exactly one archetype. The VIP spend bar is derived dynamically (75th pct of
-- buyer monetary), so cohorts adapt to the brand's actual distribution.

WITH thresholds AS (
    SELECT percentile_cont(0.75) WITHIN GROUP (ORDER BY monetary) AS vip_spend
    FROM customer_profiles
    WHERE order_count >= 1
)
SELECT
    cp.customer_id,
    CASE
        WHEN cp.order_count >= 3 AND cp.recency_days <= 30                       THEN 'loyal_regular'
        WHEN cp.monetary >= t.vip_spend AND cp.recency_days BETWEEN 31 AND 150   THEN 'lapsing_vip'
        WHEN cp.order_count = 1 AND cp.recency_days BETWEEN 14 AND 75            THEN 'at_risk_first_timer'
        WHEN cp.order_count = 1 AND cp.recency_days > 75                         THEN 'one_and_done'
        WHEN cp.order_count >= 2 AND cp.recency_days BETWEEN 31 AND 180          THEN 'repeat_winback'
        WHEN cp.recency_days > 180                                              THEN 'dormant_winback'
        ELSE 'recent_nurture'
    END AS archetype_key,
    cp.recency_days,
    cp.order_count,
    cp.monetary,
    cp.aov,
    cp.discount_dependency,
    cp.predicted_clv,
    cp.top_category,
    cp.preferred_channel,
    cp.lifecycle_stage
FROM customer_profiles cp
CROSS JOIN thresholds t
WHERE cp.order_count >= 1;
