"""multi-user: add user_id to items and categories (Supabase manages users)

user_id stores the Supabase Auth UUID. No local users table is needed —
Supabase handles auth, password hashing, and JWTs.

Revision ID: 005
Revises: 004
Create Date: 2026-03-12
"""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    # user_id on categories (nullable — existing rows get NULL until first user login)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE categories ADD COLUMN user_id UUID;
        EXCEPTION WHEN duplicate_column THEN NULL; END $$
    """)
    op.execute("ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS categories_user_name ON categories(user_id, name)"
    )

    # user_id on items
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE items ADD COLUMN user_id UUID;
        EXCEPTION WHEN duplicate_column THEN NULL; END $$
    """)
    op.execute("ALTER TABLE items DROP CONSTRAINT IF EXISTS items_url_key")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS items_user_url ON items(user_id, url)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS items_user_url")
    op.execute("DROP INDEX IF EXISTS categories_user_name")
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS user_id")
    op.execute("ALTER TABLE categories DROP COLUMN IF EXISTS user_id")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS items_url_key ON items(url)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS categories_name_key ON categories(name)")
