"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-03-04

Creates the full Stash schema:
  - pgvector extension
  - categories table (with 7 seeded defaults)
  - items table
  - vector + FTS indexes
"""

from typing import Sequence, Union
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name       TEXT NOT NULL UNIQUE,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        INSERT INTO categories (name, is_default) VALUES
            ('AI & Tech',          TRUE),
            ('Product & Design',   TRUE),
            ('Business & Finance', TRUE),
            ('World Affairs',      TRUE),
            ('Science & Health',   TRUE),
            ('Personal',           TRUE),
            ('Reference',          TRUE)
        ON CONFLICT (name) DO NOTHING
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            url         TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            content     TEXT,
            summary     TEXT,
            tags        TEXT[],
            manual_tags TEXT[] DEFAULT '{}',
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            favicon_url TEXT,
            embedding   vector(768),
            status      TEXT DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processed', 'failed')),
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS items_embedding_idx
            ON items USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS items_fts_idx
            ON items USING gin(
                to_tsvector('english', title || ' ' || COALESCE(content, ''))
            )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS items")
    op.execute("DROP TABLE IF EXISTS categories")
    op.execute("DROP EXTENSION IF EXISTS vector")
