"""
Gemini AI service: summarization, tagging, embedding generation, and RAG Q&A.

Uses the google-genai SDK (v1 API), which supports text-embedding-004 and gemini-2.5-flash.
The older google-generativeai SDK used v1beta, where text-embedding-004 was unavailable.
"""

import json
import re
from google import genai
from google.genai import types

from config import GEMINI_API_KEY

_client = genai.Client(api_key=GEMINI_API_KEY)

GENERATIVE_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# Cache query embeddings — same text always produces the same vector (deterministic).
# Capped at 512 entries to keep memory bounded (~3 MB max at 768 floats each).
_MAX_EMBEDDING_CACHE = 512
_embedding_cache: dict[str, list[float]] = {}


async def summarize(title: str, content: str, categories: list[str] | None = None) -> dict:
    """
    Ask Gemini to produce a summary, tags, and category for the given content.

    categories: dynamic list of category names from the DB.
                If omitted, falls back to a generic prompt (shouldn't happen in practice).

    Returns a dict: { summary, tags, category, error }
    Falls back to safe defaults if parsing fails, with error describing what went wrong.
    """
    # Truncate content to avoid hitting token limits on very long articles
    truncated = content[:8000] if content else ""

    if categories:
        category_list = ", ".join(f'"{c}"' for c in categories)
        category_rule = (
            f"- category: assign exactly one from this list: [{category_list}]. "
            "Choose the closest match even if unsure. Never return null or 'uncategorized'."
        )
        category_example = categories[0] if categories else "AI & Tech"
    else:
        category_rule = '- category: exactly one of "AI & Tech", "Reference", or "Personal"'
        category_example = "AI & Tech"

    prompt = f"""You are a knowledge base assistant. Analyze this content and return a JSON object.

Title: {title}

Content:
{truncated}

Return ONLY valid JSON with this exact structure:
{{
  "overview": "1-2 sentence tldr capturing the core thesis or main argument",
  "key_points": [
    "most important fact, insight, or takeaway",
    "second key point",
    "third key point"
  ],
  "tags": ["tag1", "tag2", "tag3"],
  "category": "{category_example}"
}}

Rules:
- overview: 1-2 sentences — the single most important thing to understand about this content
- key_points: 4-6 bullet points of essential details, findings, or insights a reader should retain; be specific and extract actual substance (numbers, names, conclusions), not vague generalities
- tags: 3-5 short lowercase tags (topics, not generic words like "article")
- {category_rule}
- Return ONLY the JSON, no markdown, no explanation"""

    try:
        response = await _client.aio.models.generate_content(
            model=GENERATIVE_MODEL,
            contents=prompt,
        )
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json ... ```
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        chosen_category = result.get("category", "")
        # Validate the returned category is in our list; fall back to first if not
        if categories and chosen_category not in categories:
            chosen_category = categories[0]

        # Merge overview + key_points into a single summary field (no schema change needed).
        # Format: overview paragraph, then bullet points.
        overview = result.get("overview", "")
        key_points = result.get("key_points", [])[:6]
        if key_points:
            bullets = "\n".join(f"• {p}" for p in key_points)
            full_summary = f"{overview}\n\n{bullets}" if overview else bullets
        else:
            full_summary = overview

        return {
            "summary": full_summary,
            "tags": result.get("tags", [])[:5],
            "category": chosen_category,
            "error": None,
        }
    except Exception as e:
        print(f"[gemini] summarize failed: {e}")
        fallback = categories[0] if categories else "Reference"
        return {"summary": "", "tags": [], "category": fallback, "error": str(e)}


async def generate_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional embedding vector using text-embedding-004.
    Used for semantic search via pgvector cosine similarity.
    Results are cached — same text always produces the same vector.
    """
    if text in _embedding_cache:
        return _embedding_cache[text]
    try:
        result = await _client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768,  # match pgvector schema
            ),
        )
        vector = result.embeddings[0].values
        if len(_embedding_cache) >= _MAX_EMBEDDING_CACHE:
            # Evict oldest entry (insertion-order dict since Python 3.7)
            _embedding_cache.pop(next(iter(_embedding_cache)))
        _embedding_cache[text] = vector
        return vector
    except Exception as e:
        print(f"[gemini] embedding failed: {e}")
        return []


async def item_answer(question: str, item: dict) -> str:
    """
    Answer a question about a specific saved item using its title, summary, and content.
    Returns a plain string answer.
    """
    context = f"Title: {item.get('title', '')}\n\n"
    if item.get("content"):
        # Use full content as primary context (truncated to ~12k chars to stay within token limits)
        context += f"Content:\n{item['content'][:12000]}"
    elif item.get("summary"):
        # Fall back to summary only if content hasn't been extracted yet
        context += f"Summary (full content not yet available):\n{item['summary']}"

    prompt = f"""You are a personal knowledge assistant. Answer the question using ONLY the content below.
If the answer isn't in the content, say: "I don't have enough information in this item to answer that."

{context}

Question: {question}

Answer directly and concisely. No JSON, no citations needed."""

    try:
        response = await _client.aio.models.generate_content(
            model=GENERATIVE_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[gemini] item_answer failed: {e}")
        return "Something went wrong while generating an answer. Please try again."


async def rag_answer(question: str, sources: list[dict]) -> dict:
    """
    Answer a question using ONLY the provided source summaries (RAG).

    sources: list of { id, title, url, summary }
    Returns: { answer: str, source_ids: list[str] }
    """
    if not sources:
        return {
            "answer": "I don't have information about that in your saved items.",
            "source_ids": [],
        }

    # Build context from the top retrieved items
    context_parts = []
    for i, src in enumerate(sources):
        context_parts.append(
            f"[{i+1}] ID: {src['id']}\n"
            f"Title: {src['title']}\n"
            f"Summary: {src['summary']}\n"
        )
    context = "\n".join(context_parts)

    prompt = f"""You are a personal knowledge assistant. Answer the question using ONLY the sources below.
If the answer is not in the sources, say exactly: "I don't have information about that in your saved items."

Sources:
{context}

Question: {question}

Return ONLY valid JSON:
{{
  "answer": "your answer here",
  "source_ids": ["id-of-source-used", "another-id-if-relevant"]
}}

Rules:
- Only cite sources that directly support your answer
- source_ids must be exact UUIDs from the sources above
- No markdown, no explanation outside the JSON"""

    try:
        response = await _client.aio.models.generate_content(
            model=GENERATIVE_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        result = json.loads(text)
        return {
            "answer": result.get(
                "answer", "I don't have information about that in your saved items."
            ),
            "source_ids": result.get("source_ids", []),
        }
    except Exception as e:
        print(f"[gemini] rag_answer failed: {e}")
        return {
            "answer": "Something went wrong while generating an answer. Please try again.",
            "source_ids": [],
        }
