import React from "react";

/**
 * ItemCard — white card on warm background.
 * Shows: meta row (favicon, source, category, date), title, summary, tags.
 * Clicking opens the slide-in detail panel. Delete button visible on hover.
 */
export default function ItemCard({ item, categoryName, onDelete, onClick }) {
  const date = item.created_at
    ? new Date(item.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      })
    : "";

  // Derive source domain from URL
  let source = "";
  try {
    source = new URL(item.url).hostname.replace(/^www\./, "");
  } catch {
    source = item.url;
  }

  const pending = item.status === "pending";
  const allTags = [...(item.tags || []), ...(item.manual_tags || [])];

  function handleDelete(e) {
    e.stopPropagation();
    if (window.confirm("Remove this item from your stash?")) {
      onDelete(item.id);
    }
  }

  return (
    <article className="item-card" onClick={onClick}>
      {/* Meta row */}
      <div className="item-card-meta">
        {item.favicon_url && (
          <img
            src={item.favicon_url}
            alt=""
            className="item-favicon"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
        <span className="item-source">{source}</span>
        {categoryName && (
          <span className="item-category-badge">{categoryName}</span>
        )}
        <span className="item-date">{date}</span>
      </div>

      {/* Title */}
      <h2 className="item-title">{item.title}</h2>

      {/* Summary — show only the overview line (first paragraph before bullet points) */}
      {!pending && item.summary && (
        <p className="item-summary">{item.summary.split("\n")[0]}</p>
      )}

      {/* Tags */}
      <div className="item-tags-row">
        {pending ? (
          <span className="tag-pending">Processing…</span>
        ) : (
          <>
            {(item.tags || []).slice(0, 4).map((tag) => (
              <span key={`ai-${tag}`} className="tag">{tag}</span>
            ))}
            {(item.manual_tags || []).map((tag) => (
              <span key={`manual-${tag}`} className="tag-manual">{tag}</span>
            ))}
          </>
        )}
      </div>

      <button className="delete-btn" onClick={handleDelete} title="Remove">
        ×
      </button>
    </article>
  );
}
