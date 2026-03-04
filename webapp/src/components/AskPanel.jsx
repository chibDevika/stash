import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

/**
 * AskPanel — natural language Q&A over saved items (RAG).
 * Shows the answer and links to the cited source items.
 */
export default function AskPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResult(null);
    setError("");

    try {
      const data = await api.query(question.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ask-panel">
      <h1 className="page-title">Ask a question</h1>
      <p className="ask-subtitle">
        Ask anything — the answer comes only from your saved items.
      </p>

      <form className="ask-form" onSubmit={handleSubmit}>
        <textarea
          className="ask-input"
          placeholder="e.g. What did I save about React performance?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
        />
        <button type="submit" className="ask-btn" disabled={loading || !question.trim()}>
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      {error && <p className="ask-error">{error}</p>}

      {result && (
        <div className="ask-result">
          <div className="answer-box">
            <p className="answer-text">{result.answer}</p>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="sources-section">
              <h2 className="section-label">Sources</h2>
              <ul className="sources-list">
                {result.sources.map((src) => (
                  <li key={src.id} className="source-item">
                    <Link to={`/item/${src.id}`} className="source-link">
                      {src.title}
                    </Link>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-external"
                    >
                      ↗
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
