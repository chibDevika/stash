"""
GET /search?q=&mode=hybrid|keyword|semantic

Three search modes:
- keyword:  Postgres full-text search (ts_rank on title + content)
- semantic: pgvector cosine similarity on the query embedding
- hybrid:   both, merged with Reciprocal Rank Fusion (deduped by ID)
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import gemini, db as db_service

router = APIRouter()


def reciprocal_rank_fusion(keyword_results: list, semantic_results: list, k: int = 60) -> list:
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

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [items_by_id[id_] for id_ in sorted_ids]


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$"),
    session: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_id = getattr(request.state, "user_id", None)
    keyword_results = []
    semantic_results = []

    if mode in ("keyword", "hybrid"):
        keyword_results = await db_service.keyword_search(session, q, limit=10, user_id=user_id)

    if mode in ("semantic", "hybrid"):
        embedding = await gemini.generate_embedding(q)
        if embedding:
            semantic_results = await db_service.vector_search(
                session, embedding, limit=10, user_id=user_id
            )

    if mode == "keyword":
        results = keyword_results
    elif mode == "semantic":
        results = semantic_results
    else:
        # Hybrid: keyword-first; fall back to semantic only when keyword finds nothing.
        results = keyword_results if keyword_results else semantic_results

    return {"items": results, "query": q, "mode": mode}
