"""add demo_items table

Revision ID: 002
Revises: 001
Create Date: 2025-03-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS demo_items (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            url         TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            summary     TEXT,
            tags        TEXT[],
            category    TEXT,
            source      TEXT,
            favicon_url TEXT,
            saved_date  TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS demo_items")
