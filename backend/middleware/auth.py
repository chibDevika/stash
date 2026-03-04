from fastapi import Request, HTTPException
from config import SECRET_KEY


async def verify_api_key(request: Request, call_next):
    # Skip auth for health check and all demo endpoints
    if request.url.path == "/health" or request.url.path.startswith("/demo"):
        return await call_next(request)

    # If SECRET_KEY is not set, auth is disabled (local dev convenience)
    if not SECRET_KEY:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await call_next(request)
