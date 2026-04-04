"""
JWT auth middleware — validates Supabase Bearer tokens on every protected request.

Public paths (no token required): /health, /demo/*
If SUPABASE_JWT_SECRET is not set, auth is disabled (local dev convenience).

Supports both HS256 (legacy Supabase projects) and RS256 (newer Supabase projects).
RS256 tokens are verified via Supabase's JWKS endpoint.
"""

import jwt as pyjwt
from jwt import PyJWKClient
from fastapi import Request
from fastapi.responses import JSONResponse

from config import SUPABASE_JWT_SECRET, SUPABASE_URL

_PUBLIC_PATHS = {"/health"}
_PUBLIC_PREFIXES = ("/demo",)

# Cache the JWKS client so we don't refetch keys on every request
_jwks_client: PyJWKClient | None = None

def _get_jwks_client() -> PyJWKClient | None:
    global _jwks_client
    if _jwks_client is None and SUPABASE_URL:
        jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


async def verify_token(request: Request, call_next):
    # Always pass CORS preflight through — the CORS middleware handles these.
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    # Auth disabled when no secrets configured (local dev).
    if not SUPABASE_JWT_SECRET and not SUPABASE_URL:
        request.state.user_id = None
        request.state.user = {"id": None, "email": None, "is_admin": False}
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401, content={"detail": "Missing or malformed Authorization header"}
        )

    token = auth_header[7:]

    # Peek at the header to decide which verification path to use
    try:
        unverified_header = pyjwt.get_unverified_header(token)
    except pyjwt.DecodeError as e:
        return JSONResponse(status_code=401, content={"detail": f"Malformed token: {e}"})

    alg = unverified_header.get("alg", "")

    try:
        if alg == "RS256":
            # Verify using Supabase JWKS (public key)
            jwks = _get_jwks_client()
            if not jwks:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "SUPABASE_URL not configured for RS256 verification"},
                )
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
            )
        else:
            # HS256 legacy path
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
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": f"Auth error: {e}"})

    request.state.user_id = payload["sub"]
    request.state.user = {
        "id": payload["sub"],
        "email": payload.get("email"),
        "is_admin": payload.get("app_metadata", {}).get("is_admin", False),
    }
    return await call_next(request)
