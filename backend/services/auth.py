"""
Supabase Admin API helpers — server-side user management.
These functions use the service role key and must only be called from the backend.
"""

import httpx

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

_ADMIN_BASE = f"{SUPABASE_URL}/auth/v1/admin"


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}


async def create_supabase_user(email: str, password: str, is_admin: bool = False) -> dict:
    """Create a user in Supabase Auth. Marks them as email-confirmed immediately."""
    payload: dict = {
        "email": email,
        "password": password,
        "email_confirm": True,
    }
    if is_admin:
        # is_admin in app_metadata is included in the JWT — checked by auth middleware
        payload["app_metadata"] = {"is_admin": True}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_ADMIN_BASE}/users",
            json=payload,
            headers=_auth_headers(),
        )
        if not resp.is_success:
            error_msg = resp.json().get("msg") or resp.json().get("message") or resp.text
            raise ValueError(error_msg)
        return resp.json()


async def list_supabase_users() -> list[dict]:
    """Return up to 1000 users from Supabase Auth."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_ADMIN_BASE}/users?per_page=1000",
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("users", [])
