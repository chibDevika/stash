"""
POST /save — async save pipeline.

1. Check for duplicate URL → 409 if already saved
2. Extract title + favicon immediately (fast metadata fetch)
3. Insert into DB with status='pending' — return immediately to caller
4. Queue AI processing as a FastAPI BackgroundTask:
   - Extract full content
   - Fetch categories from DB
   - Summarize + tag with Gemini (dynamic category list)
   - Generate embedding
   - Update DB with status='processed'
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, AsyncSessionLocal
from services import extractor, gemini, db as db_service

router = APIRouter()


class SaveRequest(BaseModel):
    url: str = Field(..., max_length=2000)
    title: str | None = Field(None, max_length=500)


def _validate_url(url: str) -> None:
    """Reject URLs that are not plain http/https — prevents javascript: XSS,
    file:// leaks, and SSRF against internal services."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=422,
            detail="Only HTTP and HTTPS URLs are supported.",
        )
    if not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid URL.")


@router.post("/save")
async def save_url(
    request: SaveRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    _validate_url(url)

    # Block saving browser-internal pages (belt-and-suspenders after scheme check)
    if url.startswith("chrome://") or url.startswith("chrome-extension://"):
        raise HTTPException(status_code=422, detail="Cannot save browser pages.")

    # Duplicate check — return 409 so extension can show "Already in your Stash"
    existing = await db_service.get_item_by_url(session, url)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"status": "duplicate", "message": "Already in your Stash"},
        )

    # Fast metadata extraction (title + favicon) — no content, no AI
    try:
        extracted_title, favicon_url = await extractor.extract_metadata(url)
    except Exception:
        extracted_title = url
        favicon_url = ""

    # User-provided title from extension takes precedence over auto-extracted
    title = request.title.strip() if request.title and request.title.strip() else extracted_title

    # Persist immediately with status='pending'
    item = await db_service.save_item(session, {
        "url": url,
        "title": title,
        "favicon_url": favicon_url,
    })

    # Queue full AI processing in the background
    background_tasks.add_task(process_item_ai, item["id"], url, title)

    return item


async def process_item_ai(item_id: str, url: str, title: str) -> None:
    """
    Background task: extract content, summarize, embed, update DB.
    Uses its own DB session (BackgroundTasks run after the request session closes).
    """
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Extract full content
            if extractor.is_youtube_url(url):
                extracted = await extractor.extract_youtube(url)
            else:
                extracted = await extractor.extract_article(url)

            content = extracted.get("content", "")
            # Use the richer title from extraction if we got one
            richer_title = extracted.get("title") or title

            # Step 2: Fetch category names from DB for the dynamic prompt
            categories = await db_service.list_categories(db)
            category_names = [c["name"] for c in categories]

            # Step 3: Summarize + tag with Gemini
            ai_result = await gemini.summarize(richer_title, content, category_names)

            # Step 4: Resolve category name → category_id
            category_id = None
            if ai_result.get("category"):
                matched = next(
                    (c for c in categories if c["name"] == ai_result["category"]),
                    None,
                )
                if matched:
                    category_id = matched["id"]

            # Step 5: Generate embedding on title + summary
            embedding_text = f"{richer_title} {ai_result.get('summary', '')}"
            embedding = await gemini.generate_embedding(embedding_text)

            # Step 6: Update DB with all AI data
            await db_service.update_item_ai(db, item_id, {
                "content": content,
                "summary": ai_result.get("summary", ""),
                "tags": ai_result.get("tags", []),
                "category_id": category_id,
                "embedding": embedding or None,
            })

        except Exception as e:
            print(f"[save] background AI processing failed for {item_id}: {e}")
            await db_service.mark_item_failed(db, item_id)
