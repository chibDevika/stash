import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api";

/**
 * ItemDetail — full view of a single saved item.
 * Shows summary, tags, original URL, and a link back to the list.
 */
export default function ItemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getItem(id)
      .then(setItem)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleDelete() {
    if (!window.confirm("Remove this item from your stash?")) return;
    try {
      await api.deleteItem(id);
      navigate("/");
    } catch (err) {
      alert("Could not delete item: " + err.message);
    }
  }

  if (loading) return <div className="page-loading">Loading…</div>;
  if (error) return <div className="page-error">{error}</div>;
  if (!item) return <div className="page-error">Item not found.</div>;

  const date = item.created_at
    ? new Date(item.created_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : "";

  return (
    <div className="item-detail">
      <Link to="/" className="back-link">← All items</Link>

      <div className="detail-header">
        {item.favicon_url && (
          <img
            src={item.favicon_url}
            alt=""
            className="detail-favicon"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        )}
        <div>
          <h1 className="detail-title">{item.title}</h1>
          <span className="detail-meta">
            {item.category && <span className="category-badge">{item.category}</span>}
            {date && <span className="detail-date">{date}</span>}
          </span>
        </div>
      </div>

      {item.summary && (
        <section className="detail-section">
          <h2 className="section-label">Summary</h2>
          <p className="detail-summary">{item.summary}</p>
        </section>
      )}

      {item.tags && item.tags.length > 0 && (
        <section className="detail-section">
          <h2 className="section-label">Tags</h2>
          <div className="detail-tags">
            {item.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        </section>
      )}

      {item.content && (
        <section className="detail-section">
          <h2 className="section-label">Content</h2>
          <div className="detail-content">{item.content}</div>
        </section>
      )}

      <div className="detail-actions">
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="original-link">
          View original →
        </a>
        <button className="delete-action-btn" onClick={handleDelete}>
          Remove from stash
        </button>
      </div>
    </div>
  );
}
