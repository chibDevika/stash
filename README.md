# Stash

A personal knowledge base for articles and YouTube videos. Save anything with one click, search by keyword or meaning, and ask questions answered from everything you've saved.

**Self-hosted · Bring your own Gemini API key · One command to run**

🔗 **[Live demo](https://stash-rho-one.vercel.app)** — try it without setting anything up

---

## What it does

- **Save** any article or YouTube video via a Chrome extension — returns instantly, AI runs in the background
- **Auto-organizes** into categories (AI & Tech, Science & Health, etc.) with AI-generated tags
- **Search** by keyword, semantic meaning, or hybrid — or just ask a question in plain English
- **Per-item chat** — open any saved item and ask questions scoped to that specific content
- **Manual tagging** — add your own tags to any item, filter by category

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Google Chrome (for the extension)
- A free [Gemini API key](https://aistudio.google.com)

---

## Setup (under 10 minutes)

### 1. Clone the repo

```bash
git clone https://github.com/chibDevika/stash.git
cd stash
```

### 2. Add your Gemini API key

```bash
cp .env.example .env
```

Open `.env` and fill in your Gemini API key:

```
GEMINI_API_KEY=AIzaSy...your_key_here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com) — no credit card required.

### 3. Start everything

```bash
docker-compose up --build
```

This starts three services:
- **db** — PostgreSQL with pgvector (vector search)
- **backend** — FastAPI server on port 8000
- **webapp** — React dashboard on port 3000

First run takes 2–3 minutes to build. Once you see `Application startup complete`, open **http://localhost:3000**.

### 4. Verify it's working

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 5. Load the Chrome extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode** (toggle top-right)
3. Click **Load unpacked** → select the `extension/` folder

The Stash icon will appear in your toolbar.

---

## Using Stash

### Saving content

Navigate to any article or YouTube video → click the Stash icon → click **Save this page**. The page is saved immediately (status: pending) and AI processing (summary, tags, category) runs in the background.

### Browsing your library

Open [http://localhost:3000](http://localhost:3000). Your saved items appear as cards with title, summary, tags, category, and date. Click a card to open the detail panel.

### Filtering by category

Click any category pill (AI & Tech, Science & Health, etc.) to filter. Click **+ New category** to create your own.

### Searching

Type in the search bar:
- **Keyword or phrase** → hybrid search (keyword + semantic)
- **A question** (contains `?` or starts with what/how/why) → AI answers from your saved content with citations

### Per-item chat

Click any card → in the slide-in panel, use **"Chat about this"** to ask questions scoped to that specific item only.

### Manual tags

In the detail panel, type a tag and press Enter to add it. Click `×` on any tag to remove it.

---

## Extension settings

Right-click the Stash icon → **Options** (or click the gear icon in the popup) to configure:

| Setting | Default | Description |
|---|---|---|
| Backend URL | `http://localhost:8000` | Your FastAPI backend |
| Dashboard URL | `http://localhost:3000` | Opened when you click "Open dashboard" |
| API Key | *(empty)* | Required for cloud deployments with `SECRET_KEY` set |

---

## Stopping / restarting

```bash
# Stop (data preserved in Docker volume)
docker-compose down

# Start again
docker-compose up

# Wipe all data and start fresh
docker-compose down -v && docker-compose up --build
```

---

## Troubleshooting

### "Could not connect to the backend"
- Make sure Docker Desktop is running
- Run `docker-compose up` from the stash directory
- Check: `curl http://localhost:8000/health`

### "GEMINI_API_KEY is not set"
- Confirm `.env` exists and contains your key
- Restart Docker: `docker-compose down && docker-compose up`

### Extension shows an error on YouTube
- The video must have captions available (auto-generated captions work too)
- Some videos disable transcripts entirely — these cannot be saved

### "Could not fetch the page" for articles
- Some sites block automated requests — this is a limitation of the free extraction approach
- Try a different URL from the same site

### Port conflicts
Edit `.env`:
```
BACKEND_PORT=8001
FRONTEND_PORT=3001
```
Then restart: `docker-compose down && docker-compose up`

---

## Updating

```bash
git pull
docker-compose up --build
```

Data is preserved in the Docker volume across updates.

---

## Architecture

```
Chrome extension
    └── POST /save → backend (metadata stored immediately, AI runs async)
                        ├── trafilatura (article extraction)
                        ├── youtube-transcript-api (video transcripts)
                        └── Gemini 2.5 Flash (summary · tags · category · embedding)

React webapp
    └── GET /items · GET /search · POST /query · POST /query/item/{id}
            └── PostgreSQL + pgvector (keyword FTS + cosine similarity)
```

**Backend** (Python + FastAPI + SQLAlchemy):
- `POST /save` — stores URL immediately, queues AI processing as a background task
- `GET /search` — keyword (Postgres FTS) + semantic (pgvector cosine) + hybrid (RRF merge)
- `POST /query` — embeds the question, fetches top 5 relevant items, Gemini answers from those sources
- `POST /query/item/{id}` — per-item chat, scoped to a single item's content
- `GET /categories` — list/create/delete user-defined categories
- `GET /demo/*` — read-only pre-seeded demo data, no auth required

**All your data stays local.** The only external calls are to the Gemini API.
