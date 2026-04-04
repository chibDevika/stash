"""
JWT auth middleware — validates Supabase Bearer tokens on every protected request.

Public paths (no token required): /health, /demo/*
If neither SUPABASE_JWT_SECRET nor SUPABASE_URL is set, auth is disabled (local dev).

Supports both RS256 (newer Supabase projects, verified via JWKS) and HS256 (legacy).
"""

import httpx
import jwt as pyjwt
from jwt.algorithms import RSAAlgorithm
from fastapi import Request
from fastapi.responses import JSONResponse

from config import SUPABASE_JWT_SECRET, SUPABASE_URL

_PUBLIC_PATHS = {"/health"}
_PUBLIC_PREFIXES = ("/demo",)

# Simple in-process JWKS cache: {kid: public_key}
_jwks_cache: dict = {}


async def _get_rs256_key(token: str):
    """Fetch the matching RS256 public key from Supabase JWKS, with caching."""
    header = pyjwt.get_unverified_header(token)
    kid = header.get("kid")

    if kid and kid in _jwks_cache:
        return _jwks_cache[kid]

    jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        jwks = resp.json()

    for key_data in jwks.get("keys", []):
        key_kid = key_data.get("kid")
        public_key = RSAAlgorithm.from_jwk(key_data)
        _jwks_cache[key_kid] = public_key
        if key_kid == kid:
            return public_key

    # No kid match — return first key as fallback
    if _jwks_cache:
        return next(iter(_jwks_cache.values()))
    return None


async def verify_token(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    # Auth disabled when nothing is configured (local dev)
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

    try:
        header = pyjwt.get_unverified_header(token)
    except pyjwt.DecodeError as e:
        return JSONResponse(status_code=401, content={"detail": f"Malformed token: {e}"})

    alg = header.get("alg", "")

    try:
        if alg == "RS256" and SUPABASE_URL:
            public_key = await _get_rs256_key(token)
            if not public_key:
                return JSONResponse(status_code=401, content={"detail": "Could not fetch RS256 public key"})
            payload = pyjwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="authenticated",
            )
        else:
            payload = pyjwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except pyjwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Token expired"})
    except pyjwt.InvalidSignatureError:
        return JSONResponse(status_code=401, content={"detail": "Invalid signature"})
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
