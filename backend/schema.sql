-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Categories table — replaces hardcoded category enum
CREATE TABLE IF NOT EXISTS categories (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL UNIQUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed the 7 default categories on first run
INSERT INTO categories (name, is_default) VALUES
    ('AI & Tech', TRUE),
    ('Product & Design', TRUE),
    ('Business & Finance', TRUE),
    ('World Affairs', TRUE),
    ('Science & Health', TRUE),
    ('Personal', TRUE),
    ('Reference', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Main items table
CREATE TABLE IF NOT EXISTS items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url         TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    content     TEXT,                        -- full extracted text
    summary     TEXT,                        -- 2-3 sentence AI summary
    tags        TEXT[],                      -- 3-5 AI-extracted tags
    manual_tags TEXT[] DEFAULT '{}',         -- user-added tags
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    favicon_url TEXT,
    embedding   vector(768),                 -- text-embedding-004 output (768 dimensions)
    status      TEXT DEFAULT 'pending' CHECK (status IN ('pending','processed','failed')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (cosine distance).
-- HNSW gives better recall and faster queries than ivfflat for small-to-medium datasets.
CREATE INDEX IF NOT EXISTS items_embedding_idx
    ON items USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Index for full-text search on title + content
-- manual_tags are searched at query time (array_to_string isn't IMMUTABLE so can't be indexed)
CREATE INDEX IF NOT EXISTS items_fts_idx
    ON items USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '')));
