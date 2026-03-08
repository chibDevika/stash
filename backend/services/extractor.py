"""
Content extraction service.

- Articles: trafilatura — extracts clean main text from any webpage
- YouTube: youtube-transcript-api — fetches transcript + video metadata
- PDFs: pypdf — extracts text from uploaded PDF files
"""

import re
import ipaddress
import html as html_module
import httpx
import trafilatura
from io import BytesIO
from urllib.parse import urlparse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


def _check_ssrf(url: str) -> None:
    """
    Reject requests to private/loopback addresses to prevent SSRF attacks.
    Called before any outbound HTTP fetch. Raises ValueError on violation.

    Checks hostname-based blocklist + literal IP ranges.
    Does NOT do a DNS lookup (would block the event loop) — so a crafty
    attacker who owns a domain resolving to 127.0.0.1 could theoretically
    bypass this, but that is far outside the threat model for a personal app.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Block well-known internal hostnames
    blocked_hosts = {
        "localhost",
        "metadata.google.internal",   # GCP metadata endpoint
        "169.254.169.254",            # AWS/GCP/Azure instance metadata (as hostname)
    }
    if hostname.lower() in blocked_hosts:
        raise ValueError(f"Fetching from '{hostname}' is not allowed.")

    # If the hostname is a literal IP address, check if it's private
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError(f"Fetching from private address '{hostname}' is not allowed.")
    except ValueError as e:
        # If it's our own "not allowed" error, re-raise it
        if "not allowed" in str(e):
            raise
        # Otherwise it's not a valid IP literal — it's a regular hostname, which is fine


def clean_title(title: str) -> str:
    """Remove YouTube artifacts: leading (NNN) counts and ' - YouTube' suffix."""
    title = re.sub(r'^\(\d+\)\s*', '', title)
    title = re.sub(r'\s*[-–]\s*YouTube\s*$', '', title, flags=re.IGNORECASE)
    return title.strip()


def is_youtube_url(url: str) -> bool:
    """Check if a URL points to a YouTube video."""
    return bool(re.search(r"(youtube\.com/watch|youtu\.be/)", url))


def extract_video_id(url: str) -> str | None:
    """Pull the video ID out of a YouTube URL."""
    # Handles youtube.com/watch?v=ID and youtu.be/ID
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


async def extract_youtube(url: str) -> dict:
    """
    Extract transcript and metadata from a YouTube video.

    Returns: { title, content, favicon_url, category }
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    # Fetch the transcript (handles auto-generated captions too).
    # The 1.x API uses an instance with .fetch() instead of the old static get_transcript().
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        transcript_text = " ".join(snippet.text for snippet in transcript)
    except TranscriptsDisabled:
        raise ValueError("This video has transcripts disabled — it cannot be saved.")
    except NoTranscriptFound:
        raise ValueError(
            "No transcript found for this video. "
            "Try a video with captions or auto-generated subtitles enabled."
        )
    except Exception as e:
        raise ValueError(f"Could not fetch YouTube transcript: {e}")

    # Fetch the page to get the video title
    title = f"YouTube Video ({video_id})"  # fallback
    favicon_url = "https://www.youtube.com/favicon.ico"
    try:
        _check_ssrf(url)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, follow_redirects=True)
            html = resp.text
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
            if title_match:
                title = clean_title(html_module.unescape(title_match.group(1)))
    except Exception:
        pass  # title fallback is fine

    return {
        "title": title,
        "content": transcript_text,
        "favicon_url": favicon_url,
        "category": "youtube",
    }


async def extract_metadata(url: str) -> tuple[str, str]:
    """
    Quickly fetch only the page title and favicon URL — no content extraction.
    Used for the immediate 'pending' insert before AI processing begins.
    Returns: (title, favicon_url)
    """
    from urllib.parse import urlparse

    # YouTube: use the video ID as a fast fallback title
    if is_youtube_url(url):
        video_id = extract_video_id(url)
        # We don't fetch the page here (fast path), so title gets cleaned properly
        # in the background AI task via extract_youtube which calls clean_title.
        title = f"YouTube Video ({video_id})" if video_id else url
        return title, "https://www.youtube.com/favicon.ico"

    parsed = urlparse(url)
    favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    title = url  # fallback

    try:
        _check_ssrf(url)
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Stash/1.0)"},
            )
            html = resp.text
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = html_module.unescape(title_match.group(1).strip())
    except Exception:
        pass  # fallback values are fine

    return title, favicon_url


def extract_pdf(content: bytes) -> tuple[str | None, str]:
    """
    Extract text and title from a PDF file's raw bytes.

    Returns: (title, text) where title may be None if not set in PDF metadata.
    Caller should fall back to the filename when title is None.
    """
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))

    # Title from PDF metadata if available
    title: str | None = None
    if reader.metadata and reader.metadata.title:
        title = reader.metadata.title.strip() or None

    # Join all pages, strip excess whitespace
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    text = "\n".join(pages_text)
    # Collapse runs of blank lines to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return title, text


async def extract_article(url: str) -> dict:
    """
    Extract the main text content from any article/webpage using trafilatura.

    Returns: { title, content, favicon_url, category }
    """
    try:
        _check_ssrf(url)
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Stash/1.0)"},
            )
            html = resp.text
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not fetch the page: {e}")

    # trafilatura handles paywall detection, boilerplate removal, etc.
    content = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not content:
        # Fallback: at least try to get something
        content = ""

    # Extract title from the HTML <title> tag
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = clean_title(html_module.unescape(title_match.group(1))) if title_match else url

    # Build favicon URL from the domain
    from urllib.parse import urlparse
    parsed = urlparse(url)
    favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

    return {
        "title": title,
        "content": content,
        "favicon_url": favicon_url,
        "category": "article",
    }
