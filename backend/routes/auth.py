"""
Auth routes:
  GET  /auth/me       — current user info (decoded from Supabase JWT by middleware)
  POST /admin/users   — create a user in Supabase (admin only)
  GET  /admin/users   — list users from Supabase (admin only)

Login/logout is handled entirely by Supabase on the frontend.
The backend never sees passwords — only the resulting JWT.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import auth as auth_service, db as db_service

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: str
    password: str
    is_admin: bool = False


@router.get("/auth/me")
async def get_me(request: Request):
    """Return the current user's profile (parsed from their Supabase JWT)."""
    return request.state.user


@router.post("/admin/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Create a new user in Supabase Auth and seed their default categories."""
    if not request.state.user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        supabase_user = await auth_service.create_supabase_user(
            body.email, body.password, body.is_admin
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = supabase_user["id"]
    # Seed default categories so the new user has a ready-to-use setup
    await db_service.seed_default_categories(session, user_id)

    logger.info(
        "admin %s created user %s (admin=%s)",
        request.state.user.get("email"),
        body.email,
        body.is_admin,
    )
    return {
        "id": user_id,
        "email": supabase_user.get("email"),
        "is_admin": body.is_admin,
        "created_at": supabase_user.get("created_at"),
    }


@router.get("/admin/users")
async def list_users(request: Request):
    """List all users from Supabase Auth (admin only)."""
    if not request.state.user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    users = await auth_service.list_supabase_users()
    return [
        {
            "id": u["id"],
            "email": u.get("email", ""),
            "is_admin": u.get("app_metadata", {}).get("is_admin", False),
            "created_at": u.get("created_at"),
        }
        for u in users
    ]
