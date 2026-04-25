-- AIstudyguide database schema
-- Run once against your PostgreSQL database:
--   psql -h <host> -U <user> -d <dbname> -f schema.sql

-- ─────────────────────────────────────────
-- Schemas
-- ─────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS studyguide;
CREATE SCHEMA IF NOT EXISTS pipeline;

-- ─────────────────────────────────────────
-- studyguide schema
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS studyguide.users (
    user_id    SERIAL PRIMARY KEY,
    name       TEXT        NOT NULL,
    email      TEXT        NOT NULL UNIQUE,
    password   TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS studyguide.subjects (
    subject_id   SERIAL PRIMARY KEY,
    user_id      INT         NOT NULL REFERENCES studyguide.users(user_id) ON DELETE CASCADE,
    subject_name TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS studyguide.sessions (
    session_id SERIAL PRIMARY KEY,
    subject_id INT         NOT NULL REFERENCES studyguide.subjects(subject_id) ON DELETE CASCADE,
    title      TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS studyguide.chats (
    chat_id    SERIAL PRIMARY KEY,
    session_id INT         NOT NULL REFERENCES studyguide.sessions(session_id) ON DELETE CASCADE,
    question   TEXT        NOT NULL,
    answer     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS studyguide.resources (
    resource_id SERIAL PRIMARY KEY,
    user_id     INT         NOT NULL REFERENCES studyguide.users(user_id) ON DELETE CASCADE,
    subject_id  INT         REFERENCES studyguide.subjects(subject_id) ON DELETE SET NULL,
    title       TEXT        NOT NULL,
    source_type TEXT        NOT NULL CHECK (source_type IN ('pdf', 'url', 'note')),
    file_path   TEXT,
    url         TEXT,
    raw_text    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- pipeline schema
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipeline.jobs (
    job_id          SERIAL PRIMARY KEY,
    user_id         INT         REFERENCES studyguide.users(user_id) ON DELETE SET NULL,
    session_id      INT         REFERENCES studyguide.sessions(session_id) ON DELETE SET NULL,
    prompt          TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'done', 'failed')),
    result_guide_id INT,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline.provider_outputs (
    output_id   SERIAL PRIMARY KEY,
    job_id      INT         NOT NULL REFERENCES pipeline.jobs(job_id) ON DELETE CASCADE,
    provider    TEXT        NOT NULL,
    model       TEXT,
    output_json JSONB,
    output_text TEXT,
    tokens_used INT,
    latency_ms  INT,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline.guides (
    guide_id   SERIAL PRIMARY KEY,
    job_id     INT         NOT NULL REFERENCES pipeline.jobs(job_id) ON DELETE CASCADE,
    user_id    INT         REFERENCES studyguide.users(user_id) ON DELETE SET NULL,
    session_id INT         REFERENCES studyguide.sessions(session_id) ON DELETE SET NULL,
    guide_json TEXT        NOT NULL,
    summary    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add the forward reference from jobs → guides now that guides table exists
ALTER TABLE pipeline.jobs
    ADD CONSTRAINT fk_jobs_result_guide
    FOREIGN KEY (result_guide_id) REFERENCES pipeline.guides(guide_id) ON DELETE SET NULL
    NOT VALID;

-- ─────────────────────────────────────────
-- Indexes for common lookups
-- ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_subjects_user     ON studyguide.subjects(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_subject  ON studyguide.sessions(subject_id);
CREATE INDEX IF NOT EXISTS idx_chats_session     ON studyguide.chats(session_id);
CREATE INDEX IF NOT EXISTS idx_resources_user    ON studyguide.resources(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user         ON pipeline.jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_provider_outputs_job ON pipeline.provider_outputs(job_id);
CREATE INDEX IF NOT EXISTS idx_guides_job        ON pipeline.guides(job_id);
