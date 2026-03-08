"""
Item CRUD routes:
  GET    /items                    — paginated list, optional ?category_id= filter
  GET    /items/{id}               — single item detail (includes content)
  DELETE /items/{id}               — remove an item
  PATCH  /items/{id}/title         — rename an item
  PATCH  /items/{id}/tags          — add/remove manual tags
  PATCH  /items/{id}/category      — override category
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from services import db as db_service

router = APIRouter()


class UpdateTagsRequest(BaseModel):
    add: list[str] = []
    remove: list[str] = []


class UpdateCategoryRequest(BaseModel):
    category_id: str


@router.get("/items")
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    return await db_service.list_items(session, page=page, limit=limit, category_id=category_id)


@router.get("/items/{item_id}")
async def get_item(item_id: str, session: AsyncSession = Depends(get_db)):
    item = await db_service.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, session: AsyncSession = Depends(get_db)):
    deleted = await db_service.delete_item(session, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


@router.patch("/items/{item_id}/title")
async def update_title(
    item_id: str,
    request: UpdateTitleRequest,
    session: AsyncSession = Depends(get_db),
):
    item = await db_service.update_item_title(session, item_id, request.title.strip())
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}/tags")
async def update_tags(
    item_id: str,
    request: UpdateTagsRequest,
    session: AsyncSession = Depends(get_db),
):
    item = await db_service.update_item_tags(
        session, item_id, add=request.add, remove=request.remove
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}/category")
async def update_category(
    item_id: str,
    request: UpdateCategoryRequest,
    session: AsyncSession = Depends(get_db),
):
    item = await db_service.update_item_category(session, item_id, request.category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
