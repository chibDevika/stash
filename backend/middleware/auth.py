from fastapi import Request
from fastapi.responses import JSONResponse
from config import SECRET_KEY


async def verify_api_key(request: Request, call_next):
    # Always pass through CORS preflight requests — the CORS middleware handles these,
    # but our auth middleware runs first and would block them with 401.
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip auth for health check and all demo endpoints
    if request.url.path == "/health" or request.url.path.startswith("/demo"):
        return await call_next(request)

    # If SECRET_KEY is not set, auth is disabled (local dev convenience)
    if not SECRET_KEY:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key != SECRET_KEY:
        # Return JSONResponse directly — raising HTTPException inside BaseHTTPMiddleware
        # causes Starlette to wrap it in a 500 error instead of returning 401.
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)
