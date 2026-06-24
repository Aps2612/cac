-- Measurement: control groups prove real incremental lift, not last-touch attribution.

CREATE TABLE IF NOT EXISTS outcomes (
    outcome_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    customer_id   text NOT NULL,
    cohort_id     uuid REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    holdout_group text NOT NULL,                      -- treatment | control
    converted     boolean NOT NULL DEFAULT false,
    revenue       numeric(12,2) NOT NULL DEFAULT 0,
    observed_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, customer_id)
);
CREATE INDEX IF NOT EXISTS idx_outcomes_run ON outcomes(run_id, holdout_group);
CREATE INDEX IF NOT EXISTS idx_outcomes_cohort ON outcomes(cohort_id);

CREATE TABLE IF NOT EXISTS measurements (
    run_id         uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    cohort_id      uuid REFERENCES cohorts(cohort_id) ON DELETE CASCADE,  -- NULL = overall
    scope          text NOT NULL,                     -- overall | cohort
    label          text,
    treatment_n    integer NOT NULL DEFAULT 0,
    treatment_conv integer NOT NULL DEFAULT 0,
    control_n      integer NOT NULL DEFAULT 0,
    control_conv   integer NOT NULL DEFAULT 0,
    treatment_rate numeric(8,5) NOT NULL DEFAULT 0,
    control_rate   numeric(8,5) NOT NULL DEFAULT 0,
    abs_lift       numeric(8,5) NOT NULL DEFAULT 0,
    rel_lift       numeric(8,4) NOT NULL DEFAULT 0,
    ci_low         numeric(8,5) NOT NULL DEFAULT 0,
    ci_high        numeric(8,5) NOT NULL DEFAULT 0,
    p_value        numeric(8,6) NOT NULL DEFAULT 1,
    revenue_lift   numeric(14,2) NOT NULL DEFAULT 0,
    created_at     timestamptz NOT NULL DEFAULT now()
);
-- One measurement row per (run, scope, cohort); COALESCE handles the NULL overall cohort.
CREATE UNIQUE INDEX IF NOT EXISTS uq_measurements_scope
    ON measurements (run_id, scope, COALESCE(cohort_id, '00000000-0000-0000-0000-000000000000'::uuid));
