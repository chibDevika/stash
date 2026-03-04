import React, { useState, useEffect, useRef } from "react";
import { api } from "../api";

/**
 * ItemDetailPanel — slide-in panel from the right.
 * Shows: title (linked), source, date, full AI summary,
 *        category dropdown, AI tags + manual tags with add/remove,
 *        and a "Chat about this" inline Q&A input.
 * No raw content shown.
 */
export default function ItemDetailPanel({ item, categories, onClose, onItemUpdated }) {
  const [localItem, setLocalItem] = useState(item);
  const [tagInput, setTagInput] = useState("");
  const [tagAdding, setTagAdding] = useState(false);
  const [tagError, setTagError] = useState(null);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const inputRef = useRef(null);

  // Sync when parent passes updated item
  useEffect(() => { setLocalItem(item); }, [item]);

  // Close on Escape key
  useEffect(() => {
    function handleKey(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const date = localItem.created_at
    ? new Date(localItem.created_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "";

  let source = "";
  try {
    source = new URL(localItem.url).hostname.replace(/^www\./, "");
  } catch {
    source = localItem.url;
  }

  // ── Tag management ─────────────────────────────────────────────────────────

  async function addTag(tag) {
    const t = tag.trim().toLowerCase();
    if (!t || tagAdding) return;
    setTagAdding(true);
    setTagError(null);
    try {
      const updated = await api.updateItemTags(localItem.id, [t], []);
      setLocalItem(updated);
      onItemUpdated(updated);
      setTagInput("");
    } catch (e) {
      setTagError(e.message || "Failed to add tag. Please try again.");
    } finally {
      setTagAdding(false);
    }
  }

  async function removeTag(tag, isManual) {
    if (!isManual) return; // AI tags can't be removed
    setTagError(null);
    try {
      const updated = await api.updateItemTags(localItem.id, [], [tag]);
      setLocalItem(updated);
      onItemUpdated(updated);
    } catch (e) {
      setTagError(e.message || "Failed to remove tag. Please try again.");
    }
  }

  function handleTagKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag(tagInput);
    }
  }

  // ── Category change ────────────────────────────────────────────────────────

  async function handleCategoryChange(e) {
    const categoryId = e.target.value;
    try {
      const updated = await api.updateItemCategory(localItem.id, categoryId);
      setLocalItem(updated);
      onItemUpdated(updated);
    } catch (err) {
      console.error("Failed to update category", err);
    }
  }

  // ── Per-item chat ──────────────────────────────────────────────────────────

  async function handleAsk(e) {
    e.preventDefault();
    const q = chatQuestion.trim();
    if (!q) return;
    setChatLoading(true);
    setChatAnswer(null);
    setChatError(null);
    try {
      const result = await api.queryItem(localItem.id, q);
      setChatAnswer(result.answer);
    } catch (err) {
      setChatError(err.message || "Something went wrong. Please try again.");
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <>
      {/* Semi-transparent overlay — click to close */}
      <div className="panel-overlay" onClick={onClose} />

      <aside className="detail-panel">
        {/* Header: title + close */}
        <div className="panel-header">
          <h2 className="panel-title">
            <a href={localItem.url} target="_blank" rel="noopener noreferrer">
              {localItem.title}
            </a>
          </h2>
          <button className="panel-close" onClick={onClose} title="Close">×</button>
        </div>

        <div className="panel-body">
          {/* Source + date */}
          <div className="panel-meta">
            {localItem.favicon_url && (
              <img
                src={localItem.favicon_url}
                alt=""
                style={{ width: 14, height: 14, borderRadius: 2 }}
                onError={(e) => { e.target.style.display = "none"; }}
              />
            )}
            <span>{source}</span>
            <span>·</span>
            <span>{date}</span>
          </div>

          <hr className="panel-divider" />

          {/* AI Summary — overview + key points */}
          {localItem.summary && (() => {
            const [overview, ...rest] = localItem.summary.split("\n\n");
            const bullets = rest.join("\n\n")
              .split("\n")
              .map(l => l.trim())
              .filter(l => l.startsWith("•"));
            return (
              <div>
                <div className="panel-section-label">Summary</div>
                {overview && <p className="panel-summary">{overview}</p>}
                {bullets.length > 0 && (
                  <ul className="panel-key-points">
                    {bullets.map((b, i) => (
                      <li key={i}>{b.replace(/^•\s*/, "")}</li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })()}

          {/* Category */}
          {categories.length > 0 && (
            <div>
              <div className="panel-section-label">Category</div>
              <select
                className="panel-category-select"
                value={localItem.category_id || ""}
                onChange={handleCategoryChange}
              >
                <option value="">— Uncategorized —</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Tags */}
          <div className="panel-tags-section">
            <div className="panel-section-label">Tags</div>

            {/* AI tags (non-removable) */}
            {(localItem.tags || []).length > 0 && (
              <div className="panel-tags-row">
                {(localItem.tags || []).map((tag) => (
                  <span key={`ai-${tag}`} className="tag">{tag}</span>
                ))}
              </div>
            )}

            {/* Manual tags (removable) */}
            <div className="panel-tags-row">
              {(localItem.manual_tags || []).map((tag) => (
                <span key={`manual-${tag}`} className="tag-removable tag-manual">
                  {tag}
                  <button
                    className="tag-remove"
                    onClick={() => removeTag(tag, true)}
                    title="Remove tag"
                  >
                    ×
                  </button>
                </span>
              ))}
              <span className="tag-add-row">
                <input
                  ref={inputRef}
                  className="tag-add-input"
                  placeholder="add tag…"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  disabled={tagAdding}
                />
                <button
                  className="tag-add-btn"
                  onClick={() => addTag(tagInput)}
                  disabled={tagAdding || !tagInput.trim()}
                  title="Add tag"
                >
                  {tagAdding ? "…" : "+"}
                </button>
              </span>
            </div>
            {tagError && <p className="tag-error">{tagError}</p>}
          </div>

          <hr className="panel-divider" />

          {/* Per-item chat */}
          <div>
            <div className="panel-section-label">Chat about this</div>
            <div className="item-chat">
              <form className="item-chat-input-row" onSubmit={handleAsk}>
                <input
                  className="item-chat-input"
                  placeholder="Ask something about this…"
                  value={chatQuestion}
                  onChange={(e) => setChatQuestion(e.target.value)}
                />
                <button
                  className="item-chat-btn"
                  disabled={chatLoading || !chatQuestion.trim()}
                >
                  {chatLoading ? "…" : "Ask"}
                </button>
              </form>

              {chatAnswer && (
                <div className="item-chat-answer">{chatAnswer}</div>
              )}
              {chatError && (
                <p className="item-chat-error">{chatError}</p>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
