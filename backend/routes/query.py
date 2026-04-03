"""
Query routes:
  POST /query           — RAG Q&A across the user's saved items
  POST /query/item/{id} — per-item chat (scoped to one item's content)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import gemini, db as db_service

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@router.post("/query")
async def query(request: Request, body: QueryRequest, session: AsyncSession = Depends(get_db)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    user_id = getattr(request.state, "user_id", None)

    embedding = await gemini.generate_embedding(question)
    if not embedding:
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable. Please try again shortly.",
        )

    top_items = await db_service.vector_search(session, embedding, limit=5, user_id=user_id)

    # Fetch summaries for the RAG context (scoped to the same user)
    sources = []
    for item in top_items:
        params: dict = {"id": item["id"]}
        user_cond = ""
        if user_id is not None:
            user_cond = "AND user_id = CAST(:user_id AS uuid)"
            params["user_id"] = user_id
        result = await session.execute(
            text(f"SELECT id, title, url, summary FROM items WHERE id = CAST(:id AS uuid) {user_cond}"),
            params,
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


@router.post("/query/item/{item_id}")
async def query_item(
    item_id: str,
    body: QueryRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    user_id = getattr(request.state, "user_id", None)
    item = await db_service.get_item(session, item_id, user_id=user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    answer = await gemini.item_answer(question, item)
    return {"answer": answer}
