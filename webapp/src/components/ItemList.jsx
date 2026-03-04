import React, { useEffect, useState, useCallback } from "react";
import { api } from "../api";
import SearchBar from "./SearchBar";
import ItemCard from "./ItemCard";

/**
 * ItemList — main page: search bar + paginated grid of saved items.
 * Switches between browse mode (all items) and search mode based on query.
 */
export default function ItemList() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState("hybrid");

  const LIMIT = 20;

  const loadItems = useCallback(async (p = 1) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listItems(p, LIMIT);
      setItems(data.items);
      setTotal(data.total);
      setPage(p);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadItems(1);
  }, [loadItems]);

  async function handleSearch(q, mode) {
    setSearchQuery(q);
    setSearchMode(mode);

    if (!q) {
      // Empty query — go back to full list
      loadItems(1);
      return;
    }

    setSearchLoading(true);
    setError("");
    try {
      const data = await api.search(q, mode);
      setItems(data.items);
      setTotal(data.items.length);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearchLoading(false);
    }
  }

  async function handleDelete(id) {
    try {
      await api.deleteItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err) {
      alert("Could not delete item: " + err.message);
    }
  }

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="item-list-page">
      <SearchBar onSearch={handleSearch} loading={searchLoading} />

      {error && <p className="page-error">{error}</p>}

      {loading ? (
        <div className="page-loading">Loading…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          {searchQuery
            ? `No results for "${searchQuery}"`
            : "Nothing saved yet. Use the Chrome extension to save your first article."}
        </div>
      ) : (
        <>
          {searchQuery && (
            <p className="results-count">
              {total} result{total !== 1 ? "s" : ""} for "{searchQuery}" ({searchMode})
            </p>
          )}
          <div className="item-grid">
            {items.map((item) => (
              <ItemCard key={item.id} item={item} onDelete={handleDelete} />
            ))}
          </div>

          {/* Pagination — only shown in browse mode, not search results */}
          {!searchQuery && totalPages > 1 && (
            <div className="pagination">
              <button
                disabled={page <= 1}
                onClick={() => loadItems(page - 1)}
                className="page-btn"
              >
                ← Previous
              </button>
              <span className="page-indicator">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => loadItems(page + 1)}
                className="page-btn"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
