"""
Query routes:
  POST /query           — RAG Q&A across all saved items
  POST /query/item/{id} — per-item chat (scoped to one item's content)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import gemini, db as db_service

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


# ── Global RAG Q&A ────────────────────────────────────────────────────────────

@router.post("/query")
async def query(request: QueryRequest, session: AsyncSession = Depends(get_db)):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Embed the question using the same model used for documents
    embedding = await gemini.generate_embedding(question)
    if not embedding:
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable. Please try again shortly.",
        )

    # Find top 5 most relevant items via cosine similarity
    top_items = await db_service.vector_search(session, embedding, limit=5)

    # Fetch summaries for RAG context
    from sqlalchemy import text
    sources = []
    for item in top_items:
        result = await session.execute(
            text("SELECT id, title, url, summary FROM items WHERE id = :id"),
            {"id": item["id"]},
        )
        row = result.mappings().fetchone()
        if row:
            sources.append({
                "id": str(row["id"]),
                "title": row["title"],
                "url": row["url"],
                "summary": row["summary"] or "",
            })

    rag_result = await gemini.rag_answer(question, sources)
    cited_sources = [s for s in sources if s["id"] in rag_result["source_ids"]]

    return {
        "answer": rag_result["answer"],
        "sources": cited_sources,
    }


# ── Per-item chat ─────────────────────────────────────────────────────────────

@router.post("/query/item/{item_id}")
async def query_item(
    item_id: str,
    request: QueryRequest,
    session: AsyncSession = Depends(get_db),
):
    """Answer a question scoped to a single saved item's content."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    item = await db_service.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    answer = await gemini.item_answer(question, item)
    return {"answer": answer}
