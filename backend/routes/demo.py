"""
Demo routes — no auth required.
Read-only endpoints over pre-seeded demo_items table.

GET  /demo/items        — list all demo items
GET  /demo/search?q=   — keyword search over demo items
POST /demo/query        — RAG Q&A using demo items as context (Gemini)

Rate limiting is applied here because these endpoints are unauthenticated and
/demo/query triggers real Gemini API calls — without a limit anyone could run
up the owner's API bill.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from services import gemini
from config import DEMO_MODE_ENABLED

router = APIRouter(prefix="/demo")
limiter = Limiter(key_func=get_remote_address)

# Demo data never changes — cache it in memory after the first DB read.
# Both endpoints that need it share the same cache.
_items_cache: list | None = None
_sources_cache: list | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


def _row_to_dict(row) -> dict:
    r = dict(row)
    if "id" in r:
        r["id"] = str(r["id"])
    if "saved_date" in r and r["saved_date"]:
        r["saved_date"] = r["saved_date"].isoformat()
    return r


async def _get_cached_items(session: AsyncSession) -> list:
    global _items_cache
    if _items_cache is not None:
        return _items_cache
    result = await session.execute(
        text("SELECT * FROM demo_items ORDER BY saved_date DESC")
    )
    _items_cache = [_row_to_dict(r) for r in result.mappings().all()]
    return _items_cache


async def _get_cached_sources(session: AsyncSession) -> list:
    global _sources_cache
    if _sources_cache is not None:
        return _sources_cache
    result = await session.execute(
        text("SELECT id, title, url, summary FROM demo_items ORDER BY saved_date DESC")
    )
    _sources_cache = [
        {"id": str(r["id"]), "title": r["title"], "url": r["url"], "summary": r["summary"] or ""}
        for r in result.mappings().all()
    ]
    return _sources_cache


@router.get("/items")
@limiter.limit("60/minute")
async def get_demo_items(request: Request, session: AsyncSession = Depends(get_db)):
    if not DEMO_MODE_ENABLED:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")
    return await _get_cached_items(session)


@router.get("/search")
@limiter.limit("30/minute")
async def search_demo(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200),
    session: AsyncSession = Depends(get_db),
):
    if not DEMO_MODE_ENABLED:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")

    result = await session.execute(
        text("""
            SELECT * FROM demo_items
            WHERE
                title ILIKE :q
                OR summary ILIKE :q
                OR category ILIKE :q
                OR EXISTS (
                    SELECT 1 FROM unnest(tags) t WHERE t ILIKE :q
                )
            ORDER BY saved_date DESC
            LIMIT 20
        """),
        {"q": f"%{q}%"},
    )
    rows = result.mappings().all()
    return {"items": [_row_to_dict(r) for r in rows], "query": q}


@router.post("/query")
@limiter.limit("5/minute")   # Gemini calls — strict limit to prevent cost abuse
async def query_demo(
    request: Request,
    body: QueryRequest,
    session: AsyncSession = Depends(get_db),
):
    if not DEMO_MODE_ENABLED:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")

    question = body.question.strip()

    # Use cached sources — demo data never changes
    sources = await _get_cached_sources(session)

    # Use the same RAG function — Gemini answers strictly from the provided context
    rag_result = await gemini.rag_answer(question, sources)
    cited_sources = [s for s in sources if s["id"] in rag_result["source_ids"]]

    return {
        "answer": rag_result["answer"],
        "sources": cited_sources,
    }
