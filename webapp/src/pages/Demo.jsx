import React, { useState, useEffect } from "react";
import { api } from "../api";

import DemoBanner from "../components/DemoBanner";

// ── Detect natural language questions vs keyword searches ─────────────────────
const QUESTION_PREFIX = /^(what|how|why|where|when|who|find|show|tell|explain|is|are|does|did|can|could|should|would)\b/i;
function isQuestion(q) {
  const t = q.trim();
  return t.endsWith("?") || QUESTION_PREFIX.test(t);
}

// ── Demo ItemCard ─────────────────────────────────────────────────────────────
function DemoCard({ item, onClick }) {
  const source = item.source || new URL(item.url).hostname.replace("www.", "");
  const date = item.saved_date
    ? new Date(item.saved_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
    : "";
  const summaryLine = item.summary ? item.summary.split("\n")[0] : "";

  return (
    <div className="item-card" onClick={onClick} style={{ cursor: "pointer" }}>
      <div className="card-meta">
        {item.favicon_url && (
          <img
            className="card-favicon"
            src={item.favicon_url}
            alt=""
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
        <span className="card-source">{source}</span>
        {item.category && (
          <span className="card-category-badge">{item.category}</span>
        )}
        {date && <span className="card-date-badge">{date}</span>}
      </div>

      <h3 className="card-title">{item.title}</h3>
      {summaryLine && <p className="card-summary">{summaryLine}</p>}

      {item.tags?.length > 0 && (
        <div className="card-tags">
          {item.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Demo detail panel ─────────────────────────────────────────────────────────
function DemoDetailPanel({ item, onClose }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);

  const source = item.source || new URL(item.url).hostname.replace("www.", "");
  const date = item.saved_date
    ? new Date(item.saved_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })
    : "";

  const [overview, ...rest] = (item.summary || "").split("\n\n");
  const bullets = rest.join("\n\n").split("\n").filter((l) => l.trim().startsWith("•"));

  async function handleChat(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setChatLoading(true);
    setChatError(null);
    setAnswer(null);
    try {
      const res = await api.queryDemo(question.trim());
      setAnswer(res.answer);
    } catch (err) {
      setChatError(err.message || "Something went wrong.");
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <>
      <div className="panel-overlay" onClick={onClose} />
      <div className="item-detail-panel">
        <div className="panel-header">
          <a className="panel-title-link" href={item.url} target="_blank" rel="noopener noreferrer">
            {item.title}
          </a>
          <button className="panel-close-btn" onClick={onClose} title="Close">×</button>
        </div>

        <div className="panel-meta">
          <span className="panel-source">{source}</span>
          {date && <span className="panel-date">{date}</span>}
          {item.category && <span className="panel-category-text">{item.category}</span>}
        </div>

        {/* Summary */}
        {overview && (
          <div className="panel-section">
            <div className="panel-section-label">Summary</div>
            <p className="panel-summary">{overview}</p>
            {bullets.length > 0 && (
              <ul className="panel-key-points">
                {bullets.map((b, i) => (
                  <li key={i}>{b.replace(/^•\s*/, "")}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Tags */}
        {item.tags?.length > 0 && (
          <div className="panel-section">
            <div className="panel-section-label">Tags</div>
            <div className="panel-tags">
              {item.tags.map((t) => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
          </div>
        )}

        {/* Demo chat (uses /demo/query — all demo items as context) */}
        <div className="panel-section">
          <div className="panel-section-label">Chat about this</div>
          <form className="item-chat-form" onSubmit={handleChat}>
            <input
              className="item-chat-input"
              placeholder="Ask something about this…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button
              type="submit"
              className="item-chat-btn"
              disabled={chatLoading || !question.trim()}
            >
              {chatLoading ? "…" : "Ask"}
            </button>
          </form>
          {chatError && <p className="item-chat-error">{chatError}</p>}
          {answer && <div className="item-chat-answer">{answer}</div>}
        </div>
      </div>
    </>
  );
}

// ── Demo dashboard ────────────────────────────────────────────────────────────
export default function Demo() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [searchResult, setSearchResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);

  // Derive unique categories from the data
  const categories = [...new Set(items.map((i) => i.category).filter(Boolean))].sort();

  useEffect(() => {
    api.getDemoItems()
      .then((data) => { setItems(data); setLoading(false); })
      .catch((err) => { setError(err.message); setLoading(false); });
  }, []);

  // ── Search ──────────────────────────────────────────────────────────────────
  const [query, setQuery] = useState("");
  const [qaMode, setQaMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  function handleQueryChange(e) {
    const v = e.target.value;
    setQuery(v);
    setQaMode(v.trim().length > 2 && isQuestion(v));
  }

  async function handleSearch(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setSearchLoading(true);
    try {
      if (qaMode) {
        const res = await api.queryDemo(q);
        setSearchResult({ type: "qa", query: q, answer: res.answer, sources: res.sources });
        setIsSearching(true);
      } else {
        const res = await api.searchDemo(q);
        setSearchResult({ type: "search", query: q, items: res.items || [] });
        setIsSearching(true);
      }
    } catch (err) {
      setSearchResult({ type: "error", error: err.message });
    } finally {
      setSearchLoading(false);
    }
  }

  function handleClearSearch() {
    setQuery("");
    setQaMode(false);
    setSearchResult(null);
    setIsSearching(false);
  }

  // ── Displayed items ──────────────────────────────────────────────────────────
  let displayItems = isSearching && searchResult?.type === "search"
    ? searchResult.items
    : items;

  if (activeCategory) {
    displayItems = displayItems.filter((i) => i.category === activeCategory);
  }

  return (
    <div className="app-layout">
      <DemoBanner />

      {/* TopBar */}
      <header className="top-bar">
        <span className="top-bar-logo">Stash</span>
        <span className="top-bar-count">
          {!isSearching && items.length > 0 ? `${items.length} items` : ""}
        </span>
      </header>

      <main className="main-content">
        {/* Category pills */}
        <div className="category-pills-row">
          <button
            className={`pill ${!activeCategory ? "pill--active" : ""}`}
            onClick={() => setActiveCategory(null)}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`pill ${activeCategory === cat ? "pill--active" : ""}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search bar */}
        <div className="search-bar">
          <form onSubmit={handleSearch}>
            <div className="search-input-row">
              <input
                className="search-input"
                placeholder="Search or ask a question…"
                value={query}
                onChange={handleQueryChange}
                autoComplete="off"
              />
              {query && (
                <button type="button" className="clear-btn" onClick={handleClearSearch}>×</button>
              )}
              <button className="search-btn" disabled={searchLoading || !query.trim()}>
                {searchLoading ? "…" : qaMode ? "Ask" : "Search"}
              </button>
            </div>
          </form>
          {!query && (
            <p className="search-hint">Type keywords to search, or ask a question in plain English</p>
          )}
        </div>

        {/* Q&A answer */}
        {isSearching && searchResult?.type === "qa" && (
          <div className="search-results">
            <div className="answer-box">
              <div className="answer-label">Answer</div>
              <p className="answer-text">{searchResult.answer}</p>
              {searchResult.sources?.length > 0 && (
                <>
                  <div className="sources-label">Sources</div>
                  <ul className="sources-list">
                    {searchResult.sources.map((s) => (
                      <li key={s.id}>
                        <a className="source-link" href={s.url} target="_blank" rel="noopener noreferrer">
                          {s.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        )}

        {searchResult?.type === "error" && (
          <p className="page-error">{searchResult.error}</p>
        )}

        {loading && <div className="page-loading">Loading…</div>}
        {error && <p className="page-error">{error}</p>}

        {isSearching && searchResult?.type === "search" && (
          <p className="results-count">
            {displayItems.length} result{displayItems.length !== 1 ? "s" : ""}
            {searchResult.query ? ` for "${searchResult.query}"` : ""}
          </p>
        )}

        {/* Item grid */}
        {!loading && !error && displayItems.length > 0 && (
          <div className="item-grid">
            {displayItems.map((item) => (
              <DemoCard key={item.id} item={item} onClick={() => setSelectedItem(item)} />
            ))}
          </div>
        )}

        {!loading && !error && displayItems.length === 0 && (
          <div className="empty-state">
            <p>No items found.</p>
          </div>
        )}
      </main>

      {/* Detail panel */}
      {selectedItem && (
        <DemoDetailPanel item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}
    </div>
  );
}
