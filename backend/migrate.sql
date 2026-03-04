-- migrate.sql — upgrade an existing Stash database to iteration-2 schema
-- Run this if you already have data and don't want to wipe the DB.
-- Safe to run multiple times (IF NOT EXISTS / ON CONFLICT guards).
--
-- Alternatively: docker compose down -v && docker compose up --build
-- (resets everything, OK for local dev with no data you need to keep)

-- 1. Categories table
CREATE TABLE IF NOT EXISTS categories (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL UNIQUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO categories (name, is_default) VALUES
    ('AI & Tech', TRUE),
    ('Product & Design', TRUE),
    ('Business & Finance', TRUE),
    ('World Affairs', TRUE),
    ('Science & Health', TRUE),
    ('Personal', TRUE),
    ('Reference', TRUE)
ON CONFLICT (name) DO NOTHING;

-- 2. Add new columns to items (each is idempotent via DO $$...$$)
DO $$ BEGIN
    ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending','processed','failed'));
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE items ADD COLUMN manual_tags TEXT[] DEFAULT '{}';
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE items ADD COLUMN category_id UUID REFERENCES categories(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- 3. Backfill status for existing processed items
UPDATE items SET status = 'processed'
WHERE status IS NULL AND summary IS NOT NULL AND summary != '';

-- 4. Drop the old category text column (rename it first as a safety net)
-- Uncomment the DROP after confirming the migration looks good:
-- ALTER TABLE items DROP COLUMN IF EXISTS category;

-- 5. Rebuild FTS index (manual_tags searched at query time, not indexed)
DROP INDEX IF EXISTS items_fts_idx;
CREATE INDEX items_fts_idx ON items USING gin(
    to_tsvector('english', title || ' ' || COALESCE(content, ''))
);
