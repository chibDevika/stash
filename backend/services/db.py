"""
Database operations: saving items, searching (keyword + vector), categories, and retrieval.
All functions receive an AsyncSession and return plain dicts for easy JSON serialization.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _embedding_to_str(embedding) -> str | None:
    """Convert a Python list to the '[x,y,z]' string pgvector expects via raw SQL."""
    if not embedding:
        return None
    return "[" + ",".join(str(v) for v in embedding) + "]"


def _row_to_dict(row) -> dict:
    """Convert a DB row mapping to a JSON-safe dict."""
    if row is None:
        return {}
    d = dict(row)
    if "id" in d and d["id"] is not None:
        d["id"] = str(d["id"])
    if "category_id" in d and d["category_id"] is not None:
        d["category_id"] = str(d["category_id"])
    # Exclude the raw embedding vector from API responses
    d.pop("embedding", None)
    # Convert datetime to ISO string
    if "created_at" in d and d["created_at"] is not None:
        d["created_at"] = d["created_at"].isoformat()
    # Internal search ranking scores — strip them
    d.pop("rank", None)
    d.pop("distance", None)
    return d


# ── Items ────────────────────────────────────────────────────────────────────

async def get_item_by_url(db: AsyncSession, url: str) -> dict | None:
    """Check if a URL already exists in the DB. Returns the item dict or None."""
    result = await db.execute(
        text("SELECT * FROM items WHERE url = :url"),
        {"url": url},
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row) if row else None


async def save_item(db: AsyncSession, data: dict) -> dict:
    """
    Insert a new item with status='pending' (metadata only, no AI fields yet).
    Returns the newly created item dict.
    """
    await db.execute(
        text("""
            INSERT INTO items (url, title, favicon_url, status)
            VALUES (:url, :title, :favicon_url, 'pending')
        """),
        {
            "url": data["url"],
            "title": data.get("title", ""),
            "favicon_url": data.get("favicon_url", ""),
        },
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM items WHERE url = :url"),
        {"url": data["url"]},
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row)


async def update_item_ai(db: AsyncSession, item_id: str, data: dict) -> None:
    """
    Update an item after background AI processing is complete.
    Sets summary, tags, category_id, embedding, and status='processed'.
    """
    embedding = _embedding_to_str(data.get("embedding"))
    await db.execute(
        text("""
            UPDATE items SET
                title       = COALESCE(:title, title),
                content     = :content,
                summary     = :summary,
                tags        = :tags,
                category_id = CAST(:category_id AS uuid),
                embedding   = :embedding,
                status      = 'processed'
            WHERE id = :id
        """),
        {
            "id": item_id,
            "title": data.get("title") or None,
            "content": data.get("content", ""),
            "summary": data.get("summary", ""),
            "tags": data.get("tags", []),
            "category_id": data.get("category_id"),
            "embedding": embedding,
        },
    )
    await db.commit()


async def mark_item_failed(db: AsyncSession, item_id: str) -> None:
    """Mark an item as failed when background AI processing encounters an unrecoverable error."""
    await db.execute(
        text("UPDATE items SET status = 'failed' WHERE id = :id"),
        {"id": item_id},
    )
    await db.commit()


async def list_items(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    category_id: str | None = None,
) -> dict:
    """Paginated list of all saved items, newest first. Optionally filter by category."""
    offset = (page - 1) * limit

    if category_id:
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM items WHERE category_id = CAST(:cid AS uuid)"),
            {"cid": category_id},
        )
        total = count_result.scalar()
        result = await db.execute(
            text("""
                SELECT * FROM items
                WHERE category_id = CAST(:cid AS uuid)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"cid": category_id, "limit": limit, "offset": offset},
        )
    else:
        count_result = await db.execute(text("SELECT COUNT(*) FROM items"))
        total = count_result.scalar()
        result = await db.execute(
            text("SELECT * FROM items ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset},
        )

    rows = result.mappings().fetchall()
    # Strip heavy content field from list view
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return {"items": items, "total": total}


async def get_item(db: AsyncSession, item_id: str) -> dict | None:
    """Fetch a single item by ID (includes content for per-item chat)."""
    result = await db.execute(
        text("SELECT * FROM items WHERE id = :id"),
        {"id": item_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    # _row_to_dict does NOT strip content — content is only removed in list/search helpers
    return _row_to_dict(row)


async def delete_item(db: AsyncSession, item_id: str) -> bool:
    """Delete an item by ID. Returns True if a row was actually deleted."""
    result = await db.execute(
        text("DELETE FROM items WHERE id = :id"),
        {"id": item_id},
    )
    await db.commit()
    return result.rowcount > 0


async def update_item_tags(
    db: AsyncSession, item_id: str, add: list[str], remove: list[str]
) -> dict | None:
    """
    Add or remove tags from manual_tags array.
    Uses Postgres array operators for atomic updates.
    """
    if add:
        # array_cat appends, then array_remove removes duplicates approach:
        # Use array || to append, then deduplicate by casting through unnest
        await db.execute(
            text("""
                UPDATE items
                SET manual_tags = ARRAY(
                    SELECT DISTINCT unnest(COALESCE(manual_tags, '{}') || CAST(:add AS text[]))
                )
                WHERE id = :id
            """),
            {"id": item_id, "add": add},
        )

    if remove:
        for tag in remove:
            await db.execute(
                text("""
                    UPDATE items
                    SET manual_tags = array_remove(COALESCE(manual_tags, '{}'), :tag)
                    WHERE id = :id
                """),
                {"id": item_id, "tag": tag},
            )

    await db.commit()
    result = await db.execute(
        text("SELECT * FROM items WHERE id = :id"),
        {"id": item_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


async def update_item_title(db: AsyncSession, item_id: str, title: str) -> dict | None:
    """Update the display title for an item."""
    await db.execute(
        text("UPDATE items SET title = :title WHERE id = :id"),
        {"title": title, "id": item_id},
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM items WHERE id = :id"),
        {"id": item_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


async def update_item_category(
    db: AsyncSession, item_id: str, category_id: str
) -> dict | None:
    """Override the category for an item."""
    await db.execute(
        text("UPDATE items SET category_id = CAST(:cid AS uuid) WHERE id = :id"),
        {"cid": category_id, "id": item_id},
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM items WHERE id = :id"),
        {"id": item_id},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


# ── Categories ────────────────────────────────────────────────────────────────

async def list_categories(db: AsyncSession) -> list[dict]:
    """Return all categories — defaults first, then user-created, alpha within each group."""
    result = await db.execute(
        text("""
            SELECT id, name, is_default, created_at
            FROM categories
            ORDER BY is_default DESC, name ASC
        """)
    )
    rows = result.mappings().fetchall()
    return [_row_to_dict(r) for r in rows]


async def create_category(db: AsyncSession, name: str) -> dict:
    """Create a user-defined category."""
    await db.execute(
        text("INSERT INTO categories (name, is_default) VALUES (:name, FALSE)"),
        {"name": name},
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM categories WHERE name = :name"),
        {"name": name},
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row)


async def get_category(db: AsyncSession, category_id: str) -> dict | None:
    result = await db.execute(
        text("SELECT * FROM categories WHERE id = :id"),
        {"id": category_id},
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row) if row else None


async def delete_category(db: AsyncSession, category_id: str) -> bool:
    """Delete a user-created category. Returns False if not found or is_default=True."""
    result = await db.execute(
        text("DELETE FROM categories WHERE id = :id AND is_default = FALSE"),
        {"id": category_id},
    )
    await db.commit()
    return result.rowcount > 0


# ── Search ────────────────────────────────────────────────────────────────────

async def keyword_search(db: AsyncSession, query: str, limit: int = 10) -> list[dict]:
    """Full-text search using Postgres tsvector on title + content + manual_tags."""
    result = await db.execute(
        text("""
            SELECT *, ts_rank(
                to_tsvector('english',
                    title || ' ' || COALESCE(content, '') || ' ' ||
                    array_to_string(COALESCE(manual_tags, '{}'), ' ')
                ),
                plainto_tsquery('english', :query)
            ) AS rank
            FROM items
            WHERE to_tsvector('english',
                title || ' ' || COALESCE(content, '') || ' ' ||
                array_to_string(COALESCE(manual_tags, '{}'), ' ')
            ) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """),
        {"query": query, "limit": limit},
    )
    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return items


async def vector_search(
    db: AsyncSession, embedding: list[float], limit: int = 10
) -> list[dict]:
    """Semantic search using pgvector cosine similarity (<=> operator)."""
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    result = await db.execute(
        text("""
            SELECT *, (embedding <=> CAST(:embedding AS vector)) AS distance
            FROM items
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        {"embedding": embedding_str, "limit": limit},
    )
    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return items
