"""
Category routes:
  GET    /categories        — list all (defaults first, then user-created)
  POST   /categories        — create a user-defined category
  DELETE /categories/{id}   — delete a user category (403 if is_default=True)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import db as db_service

router = APIRouter()


class CreateCategoryRequest(BaseModel):
    name: str


@router.get("/categories")
async def list_categories(session: AsyncSession = Depends(get_db)):
    return await db_service.list_categories(session)


@router.post("/categories", status_code=201)
async def create_category(
    request: CreateCategoryRequest,
    session: AsyncSession = Depends(get_db),
):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    try:
        return await db_service.create_category(session, name)
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
    return {"ok": True}
