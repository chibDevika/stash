"""
Database connection setup using SQLAlchemy async engine + asyncpg driver.
SSL is enabled automatically when connecting to Neon (detected via URL).
"""

from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL as _RAW_URL

# Convert postgres:// or postgresql:// → postgresql+asyncpg:// for async support.
# Also strip ?sslmode=... from the query string — asyncpg doesn't accept it
# and will raise TypeError: connect() got an unexpected keyword argument 'sslmode'.
# SSL is handled via connect_args={"ssl": True} instead.
def _build_async_url(raw: str) -> tuple[str, dict]:
    url = raw.replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://")
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    has_ssl = "sslmode" in params or "neon" in raw
    params.pop("sslmode", None)  # asyncpg uses connect_args ssl= instead
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))
    connect_args = {"ssl": True} if has_ssl else {}
    return clean_url, connect_args

_async_url, _connect_args = _build_async_url(_RAW_URL)

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
