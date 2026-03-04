"""Replace ivfflat vector index with HNSW for better recall and query speed.

HNSW (Hierarchical Navigable Small World) outperforms ivfflat on small-to-medium
datasets — no need to tune 'lists', and recall is higher by default.

Revision ID: 004
Revises: 003
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old ivfflat index and replace with HNSW.
    # If the index doesn't exist (fresh install already used HNSW), this is a no-op.
    op.execute("DROP INDEX IF EXISTS items_embedding_idx")
    op.execute("""
        CREATE INDEX IF NOT EXISTS items_embedding_idx
        ON items USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS items_embedding_idx")
    op.execute("""
        CREATE INDEX IF NOT EXISTS items_embedding_idx
        ON items USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
