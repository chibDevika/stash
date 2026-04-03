"""
Database operations: saving items, searching (keyword + vector), categories, and retrieval.
All functions accept an optional user_id (Supabase UUID string).
  - user_id=None  → no filter (dev mode with auth disabled — shows all data)
  - user_id=<str> → filter to that user's rows only
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Default categories seeded for every new user on first login
_DEFAULT_CATEGORIES = [
    "AI & Tech",
    "Product & Design",
    "Business & Finance",
    "World Affairs",
    "Science & Health",
    "Personal",
    "Reference",
]


def _embedding_to_str(embedding) -> str | None:
    if not embedding:
        return None
    return "[" + ",".join(str(v) for v in embedding) + "]"


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    d = dict(row)
    if "id" in d and d["id"] is not None:
        d["id"] = str(d["id"])
    if "category_id" in d and d["category_id"] is not None:
        d["category_id"] = str(d["category_id"])
    if "user_id" in d and d["user_id"] is not None:
        d["user_id"] = str(d["user_id"])
    d.pop("embedding", None)
    if "created_at" in d and d["created_at"] is not None:
        d["created_at"] = d["created_at"].isoformat()
    d.pop("rank", None)
    d.pop("distance", None)
    return d


# ── Items ─────────────────────────────────────────────────────────────────────

async def get_item_by_url(db: AsyncSession, url: str, user_id: str | None = None) -> dict | None:
    """Check if a URL already exists for this user. Returns item or None."""
    if user_id is not None:
        result = await db.execute(
            text("SELECT * FROM items WHERE url = :url AND user_id = CAST(:uid AS uuid)"),
            {"url": url, "uid": user_id},
        )
    else:
        result = await db.execute(
            text("SELECT * FROM items WHERE url = :url AND user_id IS NULL"),
            {"url": url},
        )
    row = result.mappings().fetchone()
    return _row_to_dict(row) if row else None


async def save_item(db: AsyncSession, data: dict) -> dict:
    """Insert a new item with status='pending'. data must include user_id (may be None)."""
    await db.execute(
        text("""
            INSERT INTO items (url, title, favicon_url, status, user_id)
            VALUES (:url, :title, :favicon_url, 'pending', CAST(:user_id AS uuid))
        """),
        {
            "url": data["url"],
            "title": data.get("title", ""),
            "favicon_url": data.get("favicon_url", ""),
            "user_id": data.get("user_id"),
        },
    )
    await db.commit()
    if data.get("user_id") is not None:
        result = await db.execute(
            text("SELECT * FROM items WHERE url = :url AND user_id = CAST(:uid AS uuid)"),
            {"url": data["url"], "uid": data["user_id"]},
        )
    else:
        result = await db.execute(
            text("SELECT * FROM items WHERE url = :url AND user_id IS NULL"),
            {"url": data["url"]},
        )
    row = result.mappings().fetchone()
    return _row_to_dict(row)


async def update_item_ai(db: AsyncSession, item_id: str, data: dict) -> None:
    """Update an item after background AI processing. No user_id filter — item_id is enough."""
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
            WHERE id = CAST(:id AS uuid)
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
    await db.execute(
        text("UPDATE items SET status = 'failed' WHERE id = CAST(:id AS uuid)"),
        {"id": item_id},
    )
    await db.commit()


async def list_items(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    category_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    """Paginated list of saved items, newest first. Filtered by user and optionally category."""
    offset = (page - 1) * limit
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if user_id is not None:
        conditions.append("user_id = CAST(:user_id AS uuid)")
        params["user_id"] = user_id
    if category_id:
        conditions.append("category_id = CAST(:cid AS uuid)")
        params["cid"] = category_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_result = await db.execute(text(f"SELECT COUNT(*) FROM items {where}"), params)
    total = count_result.scalar()
    result = await db.execute(
        text(f"SELECT * FROM items {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return {"items": items, "total": total}


async def get_item(db: AsyncSession, item_id: str, user_id: str | None = None) -> dict | None:
    """Fetch a single item. When user_id is set, enforces ownership."""
    params: dict = {"id": item_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    result = await db.execute(
        text(f"SELECT * FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row) if row else None


async def delete_item(db: AsyncSession, item_id: str, user_id: str | None = None) -> bool:
    params: dict = {"id": item_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    result = await db.execute(
        text(f"DELETE FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    await db.commit()
    return result.rowcount > 0


async def update_item_tags(
    db: AsyncSession,
    item_id: str,
    add: list[str],
    remove: list[str],
    user_id: str | None = None,
) -> dict | None:
    params_base: dict = {"id": item_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params_base["user_id"] = user_id

    if add:
        await db.execute(
            text(f"""
                UPDATE items
                SET manual_tags = ARRAY(
                    SELECT DISTINCT unnest(COALESCE(manual_tags, '{{}}') || CAST(:add AS text[]))
                )
                WHERE id = CAST(:id AS uuid) {user_cond}
            """),
            {**params_base, "add": add},
        )
    if remove:
        for tag in remove:
            await db.execute(
                text(f"""
                    UPDATE items
                    SET manual_tags = array_remove(COALESCE(manual_tags, '{{}}'), :tag)
                    WHERE id = CAST(:id AS uuid) {user_cond}
                """),
                {**params_base, "tag": tag},
            )

    await db.commit()
    result = await db.execute(
        text(f"SELECT * FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
        params_base,
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


async def update_item_title(
    db: AsyncSession, item_id: str, title: str, user_id: str | None = None
) -> dict | None:
    params: dict = {"title": title, "id": item_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    await db.execute(
        text(f"UPDATE items SET title = :title WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    await db.commit()
    result = await db.execute(
        text(f"SELECT * FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


async def update_item_category(
    db: AsyncSession, item_id: str, category_id: str, user_id: str | None = None
) -> dict | None:
    params: dict = {"cid": category_id, "id": item_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    await db.execute(
        text(f"UPDATE items SET category_id = CAST(:cid AS uuid) WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    await db.commit()
    result = await db.execute(
        text(f"SELECT * FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d.pop("content", None)
    return d


# ── Categories ────────────────────────────────────────────────────────────────

async def seed_default_categories(db: AsyncSession, user_id: str) -> None:
    """Create the default category set for a newly created user."""
    for name in _DEFAULT_CATEGORIES:
        await db.execute(
            text("""
                INSERT INTO categories (name, is_default, user_id)
                VALUES (:name, TRUE, CAST(:user_id AS uuid))
                ON CONFLICT DO NOTHING
            """),
            {"name": name, "user_id": user_id},
        )
    await db.commit()


async def list_categories(db: AsyncSession, user_id: str | None = None) -> list[dict]:
    """All categories for this user — defaults first, then user-created, alpha within each."""
    params: dict = {}
    user_cond = ""
    if user_id is not None:
        user_cond = "WHERE user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    result = await db.execute(
        text(f"""
            SELECT id, name, is_default, created_at
            FROM categories
            {user_cond}
            ORDER BY is_default DESC, name ASC
        """),
        params,
    )
    rows = result.mappings().fetchall()
    return [_row_to_dict(r) for r in rows]


async def create_category(
    db: AsyncSession, name: str, user_id: str | None = None
) -> dict:
    await db.execute(
        text("""
            INSERT INTO categories (name, is_default, user_id)
            VALUES (:name, FALSE, CAST(:user_id AS uuid))
        """),
        {"name": name, "user_id": user_id},
    )
    await db.commit()
    params: dict = {"name": name}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id
    result = await db.execute(
        text(f"SELECT * FROM categories WHERE name = :name {user_cond}"),
        params,
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row)


async def get_category(
    db: AsyncSession, category_id: str, user_id: str | None = None
) -> dict | None:
    params: dict = {"id": category_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id
    result = await db.execute(
        text(f"SELECT * FROM categories WHERE id = CAST(:id AS uuid) {user_cond}"),
        params,
    )
    row = result.mappings().fetchone()
    return _row_to_dict(row) if row else None


async def delete_category(
    db: AsyncSession, category_id: str, user_id: str | None = None
) -> bool:
    params: dict = {"id": category_id}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id
    result = await db.execute(
        text(f"DELETE FROM categories WHERE id = CAST(:id AS uuid) AND is_default = FALSE {user_cond}"),
        params,
    )
    await db.commit()
    return result.rowcount > 0


# ── Search ────────────────────────────────────────────────────────────────────

async def keyword_search(
    db: AsyncSession, query: str, limit: int = 10, user_id: str | None = None
) -> list[dict]:
    params: dict = {"query": query, "limit": limit}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    result = await db.execute(
        text(f"""
            SELECT *, ts_rank(
                to_tsvector('english',
                    title || ' ' || COALESCE(content, '') || ' ' ||
                    array_to_string(COALESCE(manual_tags, '{{}}'), ' ')
                ),
                plainto_tsquery('english', :query)
            ) AS rank
            FROM items
            WHERE to_tsvector('english',
                title || ' ' || COALESCE(content, '') || ' ' ||
                array_to_string(COALESCE(manual_tags, '{{}}'), ' ')
            ) @@ plainto_tsquery('english', :query)
            {user_cond}
            ORDER BY rank DESC
            LIMIT :limit
        """),
        params,
    )
    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return items


async def vector_search(
    db: AsyncSession,
    embedding: list[float],
    limit: int = 10,
    user_id: str | None = None,
) -> list[dict]:
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    params: dict = {"embedding": embedding_str, "limit": limit}
    user_cond = ""
    if user_id is not None:
        user_cond = "AND user_id = CAST(:user_id AS uuid)"
        params["user_id"] = user_id

    result = await db.execute(
        text(f"""
            SELECT *, (embedding <=> CAST(:embedding AS vector)) AS distance
            FROM items
            WHERE embedding IS NOT NULL
            {user_cond}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        params,
    )
    rows = result.mappings().fetchall()
    items = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("content", None)
        items.append(d)
    return items
