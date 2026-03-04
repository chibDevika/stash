"""
Database connection setup using SQLAlchemy async engine + asyncpg driver.
SSL is enabled automatically when connecting to Neon (detected via URL).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL as _RAW_URL

# Convert postgres:// or postgresql:// → postgresql+asyncpg:// for async support
_async_url = (
    _RAW_URL
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("postgres://", "postgresql+asyncpg://")
)

# asyncpg connect_args: enable SSL for Neon (and any other cloud Postgres)
_connect_args = {"ssl": True} if "neon" in _RAW_URL or "sslmode" in _RAW_URL else {}

engine = create_async_engine(
    _async_url,
    echo=False,           # set True to log SQL during development
    pool_size=5,
    max_overflow=2,
    pool_recycle=300,     # recycle connections every 5 min (avoids stale connections)
    pool_pre_ping=True,   # test connection before use — critical for cloud DBs
    connect_args=_connect_args,
)

# Factory for creating async sessions
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """FastAPI dependency — yields a DB session and closes it when done."""
    async with AsyncSessionLocal() as session:
        yield session
