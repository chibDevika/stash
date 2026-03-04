"""
Central configuration — all settings read from environment variables.
Import from here instead of calling os.environ/os.getenv directly in service files.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Required
GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]

# Database — Docker default used locally; set to Neon URL in production
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", "postgresql://stash:stash@db:5432/stash"
)

# CORS — comma-separated list of allowed frontend origins
# Local:      http://localhost:3000
# Production: https://your-app.vercel.app,chrome-extension://your-extension-id
ALLOWED_ORIGINS: list[str] = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

# Environment
ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")

# Auth — secret key for owner access.
# If empty/unset, auth is disabled (convenient for local dev).
# Set a long random string in production: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY: str = os.environ.get("SECRET_KEY", "")

# Demo mode — always enabled; separate read-only data, no auth required
DEMO_MODE_ENABLED: bool = os.environ.get("DEMO_MODE_ENABLED", "true").lower() == "true"
