import React, { useState } from "react";
import { api } from "../api";

// Detect natural language questions vs keyword searches.
// Questions → RAG answer from all items. Keywords → hybrid search.
const QUESTION_PREFIX = /^(what|how|why|where|when|who|find|show|tell|explain|is|are|does|did|can|could|should|would)\b/i;

function isQuestion(q) {
  const t = q.trim();
  return t.endsWith("?") || QUESTION_PREFIX.test(t);
}

export default function SearchBar({ onResults, onClear }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [qaMode, setQaMode] = useState(false);

  function handleChange(e) {
    const v = e.target.value;
    setQuery(v);
    setQaMode(v.trim().length > 2 && isQuestion(v));
    if (v === "") onClear();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    try {
      if (qaMode) {
        // Natural language question → RAG answer with citations
        const result = await api.query(q);
        onResults({ type: "qa", query: q, answer: result.answer, sources: result.sources });
      } else {
        // Keyword/phrase → hybrid search (keyword + semantic, best of both)
        const result = await api.search(q, "hybrid");
        onResults({ type: "search", query: q, items: result.items || result });
      }
    } catch (err) {
      onResults({ type: "error", error: err.message });
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setQuery("");
    setQaMode(false);
    onClear();
  }

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit}>
        <div className="search-input-row">
          <input
            className="search-input"
            placeholder="Search or ask a question…"
            value={query}
            onChange={handleChange}
            autoComplete="off"
          />
          {query && (
            <button type="button" className="clear-btn" onClick={handleClear} title="Clear">
              ×
            </button>
          )}
          <button className="search-btn" disabled={loading || !query.trim()}>
            {loading ? "…" : qaMode ? "Ask" : "Search"}
          </button>
        </div>
      </form>
      {/* Subtle hint under the input so users know it does both */}
      {!query && (
        <p className="search-hint">
          Type keywords to search, or ask a question in plain English
        </p>
      )}
      {query && qaMode && (
        <p className="search-hint search-hint--qa">
          Answering from your saved items
        </p>
      )}
    </div>
  );
}
