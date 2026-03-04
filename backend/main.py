"""
Stash Backend — FastAPI entry point.

Registers all routes and configures CORS so the React webapp (localhost:3000)
and the Chrome extension can both call the API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from config import ALLOWED_ORIGINS, SECRET_KEY, ENVIRONMENT
from middleware.auth import verify_api_key
from routes import save, items, search, query, categories, health, demo

# ── Startup guard ─────────────────────────────────────────────────────────────
# Fail fast if someone deploys to production without setting a SECRET_KEY.
if ENVIRONMENT == "production" and not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY must be set in production — auth is currently disabled.\n"
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# ── Rate limiter (shared instance) ────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Stash API",
    description="Personal knowledge base backend — save, search, and recall anything.",
    version="2.0.0",
)

# Attach rate limiter state so slowapi decorators work across routers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security headers ──────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Tell browsers to only use HTTPS for the next year (safe once on Railway)
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Origins read from ALLOWED_ORIGINS env var (comma-separated).
# Defaults to localhost:3000 for local dev.
# Set to your Vercel URL + extension ID in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(verify_api_key)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(save.router)
app.include_router(items.router)
app.include_router(search.router)
app.include_router(query.router)
app.include_router(categories.router)
app.include_router(demo.router)
