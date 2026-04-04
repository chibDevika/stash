# Stash

A personal knowledge base for articles, YouTube videos, and PDFs. Save anything with one click, search by keyword or meaning, and ask questions answered from everything you've saved.

**Self-hosted · Bring your own Gemini API key · Open source**

🔗 **[Live demo](https://stash-rho-one.vercel.app)** — try it without setting anything up

---

## What it does

- **Save** any article, YouTube video, or PDF — returns instantly, AI runs in the background
- **Auto-organizes** into categories with AI-generated tags and summaries
- **Search** by keyword, semantic meaning, or hybrid — or ask a question in plain English
- **Per-item chat** — open any saved item and ask questions scoped to that specific content
- **Manual tagging** — add your own tags, filter by category

---

## Quickstart (hosted)

The easiest way to use Stash is against the hosted deployment — no server setup required.

### 1. Create an account

Go to **[stash-rho-one.vercel.app](https://stash-rho-one.vercel.app)** → click **Create an account** → sign up with email.

### 2. Add your Gemini API key

Get a free key at [aistudio.google.com](https://aistudio.google.com) (no credit card required), then paste it in **Settings** inside the app.

### 3. Install the Chrome extension

The extension is not on the Web Store yet — load it manually:

1. [Download this repo](https://github.com/chibDevika/stash/archive/refs/heads/main.zip) and unzip it (or `git clone`)
2. Open Chrome → go to `chrome://extensions`
3. Enable **Developer mode** (toggle, top-right)
4. Click **Load unpacked** → select the `extension/` folder

The Stash icon will appear in your toolbar.

### 4. Configure the extension

Right-click the Stash icon → **Options**:

| Setting       | Value                                             |
| ------------- | ------------------------------------------------- |
| Backend URL   | `https://stash-backend-production.up.railway.app` |
| Dashboard URL | `https://stash-rho-one.vercel.app`                |

Click **Save settings**.

### 5. Start saving

Navigate to any article, YouTube video, or PDF → click the Stash icon → **Save this page**.

---

## Self-hosting

Deploy your own instance on Railway (backend) + Vercel (frontend) + Supabase (auth + DB).

### What you'll need

- A [Supabase](https://supabase.com) project (free tier)
- A [Railway](https://railway.app) account
- A [Vercel](https://vercel.com) account
- A free [Gemini API key](https://aistudio.google.com)

### 1. Supabase — set up auth and database

1. Create a new Supabase project
2. Go to **Settings → API** and note your:
   - **Project URL** (`https://xxxx.supabase.co`)
   - **Anon/public key**
   - **JWT Secret** (under JWT Settings)
   - **Service role key** (under API keys — keep this secret)
3. Go to **Settings → Database** and note the **Connection string** (URI format)

### 2. Railway — deploy the backend

1. Fork or push this repo to GitHub
2. Create a new Railway project → **Deploy from GitHub repo** → select your fork
3. Set the root directory to `backend/`
4. Add these environment variables in Railway:

```
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=your_supabase_connection_string
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_JWT_SECRET=your_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
ALLOWED_ORIGINS=https://your-app.vercel.app
ENVIRONMENT=production
DEMO_MODE_ENABLED=true
```

Railway will auto-deploy using `backend/railway.json`. Note your Railway backend URL once deployed.

### 3. Vercel — deploy the frontend

1. Import the repo in Vercel → set the root directory to `webapp/`
2. Add these environment variables:

```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_BACKEND_URL=https://your-backend.up.railway.app
```

3. Deploy. Note your Vercel frontend URL.
4. Go back to Railway and update `ALLOWED_ORIGINS` to your Vercel URL.

### 4. Install and configure the extension

Follow steps 3–4 from [Quickstart](#quickstart-hosted) above, but use your own Railway and Vercel URLs.

---

## Local development

```bash
git clone https://github.com/chibDevika/stash.git
cd stash

# Backend (port 8000)
cd backend
pip install -r requirements.txt
# Create a .env file with at minimum: GEMINI_API_KEY=your_key
uvicorn main:app --reload

# Frontend (port 3000) — in a separate terminal
cd webapp
npm install
# Create webapp/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
npm run dev
```

Auth is disabled in local dev if `SUPABASE_JWT_SECRET` is not set — all endpoints are open.

---

## Using Stash

### Saving content

Navigate to any article, YouTube video, or PDF → click the Stash icon → **Save this page**. The item is saved immediately and AI processing (summary, tags, category) runs in the background.

You can also drag and drop a PDF directly onto the dashboard.

### Browsing your library

Open the dashboard. Items appear as cards with title, summary, tags, category, and date. Click a card to open the detail panel.

### Filtering

Click any category pill to filter. Click **+ New category** to create your own.

### Searching

Type in the search bar:

- **Keyword or phrase** → hybrid search (keyword + semantic)
- **A question** (contains `?` or starts with what/how/why/etc.) → AI answers from your saved content with citations

### Per-item chat

Click any card → use **"Chat about this"** in the slide-in panel to ask questions scoped to that item only.

---

## Saving from iPhone

Use an iOS Shortcut that calls the API directly:

1. Open the **Shortcuts** app → tap **+**
2. Add action: **Receive** [URLs] from Share Sheet
3. Add action: **Get URLs from** Shortcut Input
4. Add action: **Get Contents of URL**
   - URL: `https://your-railway-url.up.railway.app/save`
   - Method: **POST**
   - Headers: `Content-Type` = `application/json`
   - Request Body: **JSON** → add field `url` = [URLs variable from step 3]
5. Add action: **Show Notification** → `Saved to Stash ✓`
6. Rename to **Stash** → enable **"Show in Share Sheet"**

From any app → tap **Share** → tap **Stash** → done.

---

## Architecture

```
Chrome extension / iOS Shortcut
    └── POST /save → backend (stored immediately, AI runs async)
                        ├── trafilatura (article extraction)
                        ├── youtube-transcript-api (video transcripts)
                        ├── pypdf (PDF text extraction)
                        └── Gemini 2.5 Flash (summary · tags · category · embedding)

React webapp
    └── GET /items · GET /search · POST /query · POST /query/item/{id}
            └── PostgreSQL + pgvector (keyword FTS + cosine similarity)
```

**Auth**: Supabase handles signup/login. The backend validates Supabase JWTs on every request. Demo endpoints (`/demo/*`) are always public.

**All your data stays in your own database.** The only external calls are to the Gemini API.
