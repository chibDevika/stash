"""
Category routes:
  GET    /categories        — list all (defaults first, then user-created)
  POST   /categories        — create a user-defined category
  DELETE /categories/{id}   — delete a user category (403 if is_default=True)

Auto-seeds default categories on first access for a new authenticated user.
Cache is keyed by user_id (5-minute TTL per user).
"""

import time
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import db as db_service

router = APIRouter()

_TTL = 300  # 5 minutes
_cache: dict = {}     # user_id -> list[dict]
_cached_at: dict = {} # user_id -> float


def _invalidate(user_id):
    _cache.pop(user_id, None)
    _cached_at.pop(user_id, None)


class CreateCategoryRequest(BaseModel):
    name: str


@router.get("/categories")
async def list_categories(request: Request, session: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    cache_key = user_id

    if cache_key in _cache and (time.monotonic() - _cached_at.get(cache_key, 0)) < _TTL:
        return _cache[cache_key]

    result = await db_service.list_categories(session, user_id=user_id)

    # Auto-seed defaults on first access for a new authenticated user
    if not result and user_id is not None:
        await db_service.seed_default_categories(session, user_id)
        result = await db_service.list_categories(session, user_id=user_id)

    _cache[cache_key] = result
    _cached_at[cache_key] = time.monotonic()
    return result


@router.post("/categories", status_code=201)
async def create_category(
    request_body: CreateCategoryRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    name = request_body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    try:
        created = await db_service.create_category(session, name, user_id=user_id)
        _invalidate(user_id)
        return created
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Category already exists")
        raise HTTPException(status_code=500, detail="Could not create category")


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    category = await db_service.get_category(session, category_id, user_id=user_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("is_default"):
        raise HTTPException(status_code=403, detail="Cannot delete a default category")

    deleted = await db_service.delete_category(session, category_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    _invalidate(user_id)
    return {"ok": True}
