CREATE TABLE IF NOT EXISTS lead_records (
  id BIGSERIAL PRIMARY KEY,
  client_id TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'telegram',
  telegram_user_id BIGINT NOT NULL,
  telegram_chat_id BIGINT NOT NULL,
  language TEXT NOT NULL DEFAULT 'ru',
  intent TEXT,
  timeline TEXT,
  budget TEXT,
  contact TEXT,
  score INTEGER NOT NULL DEFAULT 0,
  warmth TEXT NOT NULL DEFAULT 'cold',
  qualification TEXT NOT NULL DEFAULT 'not_qualified',
  risk_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
  handoff_status TEXT NOT NULL DEFAULT 'none',
  summary TEXT,
  transcript JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  handoff_created_at TIMESTAMPTZ,
  first_human_reply_at TIMESTAMPTZ,
  handoff_alerted_at TIMESTAMPTZ,
  claimed_by_user_id BIGINT,
  claimed_by_username TEXT,
  claimed_by_name TEXT,
  UNIQUE (client_id, telegram_user_id)
);

CREATE INDEX IF NOT EXISTS idx_lead_records_client_status ON lead_records (client_id, handoff_status);
CREATE INDEX IF NOT EXISTS idx_lead_records_user ON lead_records (telegram_user_id);
ALTER TABLE lead_records
  ADD COLUMN IF NOT EXISTS handoff_alerted_at TIMESTAMPTZ;
ALTER TABLE lead_records
  ADD COLUMN IF NOT EXISTS claimed_by_user_id BIGINT;
ALTER TABLE lead_records
  ADD COLUMN IF NOT EXISTS claimed_by_username TEXT;
ALTER TABLE lead_records
  ADD COLUMN IF NOT EXISTS claimed_by_name TEXT;
