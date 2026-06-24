-- Orchestration ledger: makes the pipeline crash-safe, idempotent, and resumable,
-- and guarantees we never double-send.

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    objective     text NOT NULL,
    as_of         timestamptz NOT NULL,
    status        text NOT NULL DEFAULT 'running',   -- running | completed | failed
    current_stage text,
    params        jsonb NOT NULL DEFAULT '{}'::jsonb,
    stats         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz
);
CREATE INDEX IF NOT EXISTS idx_runs_created ON pipeline_runs(created_at DESC);

CREATE TABLE IF NOT EXISTS pipeline_stages (
    run_id      uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    stage       text NOT NULL,
    status      text NOT NULL DEFAULT 'pending',      -- pending | running | completed | failed
    started_at  timestamptz,
    finished_at timestamptz,
    info        jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (run_id, stage)
);

CREATE TABLE IF NOT EXISTS cohorts (
    cohort_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    key         text NOT NULL,                        -- archetype key, e.g. lapsing_vip
    name        text NOT NULL,
    description text,
    size        integer NOT NULL DEFAULT 0,
    stats       jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (run_id, key)
);

CREATE TABLE IF NOT EXISTS cohort_members (
    run_id      uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    cohort_id   uuid NOT NULL REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    customer_id text NOT NULL,
    PRIMARY KEY (run_id, customer_id)                 -- one cohort per customer per run
);
CREATE INDEX IF NOT EXISTS idx_cohort_members_cohort ON cohort_members(cohort_id);

CREATE TABLE IF NOT EXISTS cohort_strategies (
    cohort_id  uuid PRIMARY KEY REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    run_id     uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    strategy   jsonb NOT NULL,
    provider   text NOT NULL,
    model      text,
    tokens     integer NOT NULL DEFAULT 0,
    cost_usd   numeric(12,6) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    customer_id       text NOT NULL,
    cohort_id         uuid REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    action            text NOT NULL,                  -- send | suppress
    channel           text,
    product_id        text,
    offer             jsonb,
    message           jsonb,
    scheduled_for     timestamptz,
    holdout_group     text,                           -- treatment | control
    status            text NOT NULL DEFAULT 'pending',-- pending | allowed | suppressed | dispatched
    suppressed_reason text,
    instruction       jsonb,                          -- the final dispatch JSON
    created_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, customer_id)                      -- exactly one decision per customer per run
);
CREATE INDEX IF NOT EXISTS idx_decisions_run ON decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(run_id, status);
CREATE INDEX IF NOT EXISTS idx_decisions_cohort ON decisions(cohort_id);

CREATE TABLE IF NOT EXISTS sends (
    send_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              uuid NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    decision_id         uuid NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
    customer_id         text NOT NULL,
    channel             text NOT NULL,
    idempotency_key     text NOT NULL UNIQUE,         -- the no-double-send guarantee
    provider            text NOT NULL,
    provider_message_id text,
    instruction         jsonb NOT NULL,
    dispatched_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sends_customer ON sends(customer_id, dispatched_at);
CREATE INDEX IF NOT EXISTS idx_sends_run ON sends(run_id);
