"""ensure items columns exist (Iteration 2 schema upgrade)

Revision ID: 003
Revises: 002
Create Date: 2025-03-04

Safe to run on any DB state:
- If items table was created in Iteration 1, adds the missing columns.
- If items table was created by migration 001, these are no-ops (IF NOT EXISTS).
- Also ensures categories table + seed data exist for Iteration 1 DBs.
"""

from typing import Sequence, Union
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Ensure categories table exists (Iteration 1 DBs won't have it)
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

    # Step 2: Add missing columns to items (safe: IF NOT EXISTS)
    op.execute("""
        ALTER TABLE items
            ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'
                CHECK (status IN ('pending', 'processed', 'failed'))
    """)

    op.execute("""
        ALTER TABLE items
            ADD COLUMN IF NOT EXISTS manual_tags TEXT[] DEFAULT '{}'
    """)

    # category_id FK references categories — categories must exist first (done above)
    op.execute("""
        ALTER TABLE items
            ADD COLUMN IF NOT EXISTS category_id UUID
                REFERENCES categories(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS category_id")
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS manual_tags")
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS status")
