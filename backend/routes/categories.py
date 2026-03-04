"""
Category routes:
  GET    /categories        — list all (defaults first, then user-created)
  POST   /categories        — create a user-defined category
  DELETE /categories/{id}   — delete a user category (403 if is_default=True)
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import db as db_service

router = APIRouter()

# Simple TTL cache — categories rarely change, no point hitting DB on every page load.
# Invalidated explicitly whenever the list is mutated (create / delete).
_TTL = 300  # 5 minutes
_cache: list | None = None
_cached_at: float = 0


def _invalidate():
    global _cache, _cached_at
    _cache = None
    _cached_at = 0


class CreateCategoryRequest(BaseModel):
    name: str


@router.get("/categories")
async def list_categories(session: AsyncSession = Depends(get_db)):
    global _cache, _cached_at
    if _cache is not None and (time.monotonic() - _cached_at) < _TTL:
        return _cache
    result = await db_service.list_categories(session)
    _cache = result
    _cached_at = time.monotonic()
    return result


@router.post("/categories", status_code=201)
async def create_category(
    request: CreateCategoryRequest,
    session: AsyncSession = Depends(get_db),
):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    try:
        created = await db_service.create_category(session, name)
        _invalidate()
        return created
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Category already exists")
        raise HTTPException(status_code=500, detail="Could not create category")


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, session: AsyncSession = Depends(get_db)):
    # Check if it's a default category — those are protected
    category = await db_service.get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("is_default"):
        raise HTTPException(status_code=403, detail="Cannot delete a default category")

    deleted = await db_service.delete_category(session, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    _invalidate()
    return {"ok": True}
