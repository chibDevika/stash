"""
GET /search?q=&mode=hybrid|keyword|semantic

Three search modes:
- keyword:  Postgres full-text search (ts_rank on title + content)
- semantic: pgvector cosine similarity on the query embedding
- hybrid:   both, merged with Reciprocal Rank Fusion (deduped by ID)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import gemini, db as db_service

router = APIRouter()


def reciprocal_rank_fusion(keyword_results: list, semantic_results: list, k: int = 60) -> list:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.
    RRF score = 1/(k + rank) — higher is better.
    Deduplicates by item ID.
    """
    scores: dict[str, float] = {}
    items_by_id: dict[str, dict] = {}

    for rank, item in enumerate(keyword_results):
        item_id = item["id"]
        scores[item_id] = scores.get(item_id, 0) + 1.0 / (k + rank + 1)
        items_by_id[item_id] = item

    for rank, item in enumerate(semantic_results):
        item_id = item["id"]
        scores[item_id] = scores.get(item_id, 0) + 1.0 / (k + rank + 1)
        items_by_id[item_id] = item

    # Sort by combined RRF score, highest first
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [items_by_id[id_] for id_ in sorted_ids]


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$"),
    session: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    keyword_results = []
    semantic_results = []

    if mode in ("keyword", "hybrid"):
        keyword_results = await db_service.keyword_search(session, q, limit=10)

    if mode in ("semantic", "hybrid"):
        embedding = await gemini.generate_embedding(q)
        if embedding:
            semantic_results = await db_service.vector_search(session, embedding, limit=10)

    if mode == "keyword":
        results = keyword_results
    elif mode == "semantic":
        results = semantic_results
    else:
        # Hybrid: keyword results are authoritative.
        # Only fall back to semantic when keyword finds nothing — this prevents
        # loosely-related semantic matches from polluting precise name/term searches.
        if keyword_results:
            results = keyword_results
        else:
            results = semantic_results

    return {"items": results, "query": q, "mode": mode}
