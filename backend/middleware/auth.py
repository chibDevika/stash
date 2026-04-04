"""
JWT auth middleware — validates Supabase Bearer tokens on every protected request.

Public paths (no token required): /health, /demo/*
If SUPABASE_JWT_SECRET is not set, auth is disabled (local dev convenience).
"""

import jwt as pyjwt
from fastapi import Request
from fastapi.responses import JSONResponse

from config import SUPABASE_JWT_SECRET

_PUBLIC_PATHS = {"/health"}
_PUBLIC_PREFIXES = ("/demo",)


async def verify_token(request: Request, call_next):
    # Always pass CORS preflight through — the CORS middleware handles these.
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    # Auth disabled when SUPABASE_JWT_SECRET is not configured (local dev).
    if not SUPABASE_JWT_SECRET:
        request.state.user_id = None
        request.state.user = {"id": None, "email": None, "is_admin": False}
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401, content={"detail": "Missing or malformed Authorization header"}
        )

    token = auth_header[7:]
    try:
        payload = pyjwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token expired"})
    except pyjwt.InvalidSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Invalid signature — wrong JWT secret"})
    except pyjwt.InvalidAudienceError:
        return JSONResponse(status_code=401, content={"detail": "Invalid audience claim"})
    except pyjwt.DecodeError as e:
        return JSONResponse(status_code=401, content={"detail": f"Decode error: {e}"})
    except pyjwt.InvalidTokenError as e:
        return JSONResponse(status_code=401, content={"detail": f"Invalid token: {e}"})

    request.state.user_id = payload["sub"]
    request.state.user = {
        "id": payload["sub"],
        "email": payload.get("email"),
        # is_admin is stored in Supabase app_metadata, set when creating the user
        "is_admin": payload.get("app_metadata", {}).get("is_admin", False),
    }
    return await call_next(request)
