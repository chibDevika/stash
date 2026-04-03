import React, { useState, useEffect, useCallback } from "react";
import { supabase } from "./lib/supabase";
import { api } from "./api";

import TopBar from "./components/TopBar";
import InstallBanner from "./components/InstallBanner";
import CategoryPills from "./components/CategoryPills";
import SearchBar from "./components/SearchBar";
import ItemCard from "./components/ItemCard";
import ItemDetailPanel from "./components/ItemDetailPanel";
import EmptyState from "./components/EmptyState";
import PdfDropZone from "./components/PdfDropZone";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Demo from "./pages/Demo";

const PAGE_SIZE = 20;

const CATS_CACHE_KEY = "stash_categories_v1";
const CATS_TTL_MS = 5 * 60 * 1000;

function loadCachedCategories() {
  try {
    const raw = localStorage.getItem(CATS_CACHE_KEY);
    if (!raw) return null;
    const { data, at } = JSON.parse(raw);
    return Date.now() - at < CATS_TTL_MS ? data : null;
  } catch {
    return null;
  }
}

function persistCategories(cats) {
  try {
    localStorage.setItem(
      CATS_CACHE_KEY,
      JSON.stringify({ data: cats, at: Date.now() }),
    );
  } catch {}
}

function bustCategoriesCache() {
  try {
    localStorage.removeItem(CATS_CACHE_KEY);
  } catch {}
}

export default function App() {
  // ── View routing: 'loading' | 'landing' | 'login' | 'demo' | 'dashboard' ───
  const [view, setView] = useState("loading");

  // ── Data state ──────────────────────────────────────────────────────────────
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ── Categories ──────────────────────────────────────────────────────────────
  const [categories, setCategories] = useState([]);
  const [activeCategoryId, setActiveCategoryId] = useState(null);

  const categoryMap = Object.fromEntries(categories.map((c) => [c.id, c.name]));

  // ── Search / Q&A state ──────────────────────────────────────────────────────
  const [searchResult, setSearchResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  // ── Detail panel ────────────────────────────────────────────────────────────
  const [selectedItem, setSelectedItem] = useState(null);

  // ── Supabase auth state ──────────────────────────────────────────────────────
  useEffect(() => {
    // Check for an existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setView(session ? "dashboard" : "landing");
    });

    // Listen for sign-in / sign-out events
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        bustCategoriesCache();
        setView("dashboard");
      } else {
        bustCategoriesCache();
        setItems([]);
        setCategories([]);
        setView("landing");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // ── Load categories ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (view !== "dashboard") return;
    const cached = loadCachedCategories();
    if (cached) setCategories(cached);
    api
      .getCategories()
      .then((cats) => {
        setCategories(cats);
        persistCategories(cats);
      })
      .catch(() => {});
  }, [view]);

  // ── Load items ──────────────────────────────────────────────────────────────
  const loadItems = useCallback(async (p = 1, catId = null) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listItems(p, PAGE_SIZE, catId);
      setItems(data.items || []);
      setTotal(data.total ?? null);
      setPage(p);
    } catch (err) {
      setError(err.message || "Failed to load items.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (view !== "dashboard") return;
    if (!isSearching) {
      loadItems(1, activeCategoryId);
    }
  }, [view, activeCategoryId, isSearching, loadItems]);

  // ── Category actions ────────────────────────────────────────────────────────
  function handleSelectCategory(id) {
    setActiveCategoryId(id);
    setSearchResult(null);
    setIsSearching(false);
  }

  function handleCategoryCreated(cat) {
    setCategories((prev) => {
      const updated = [...prev, cat];
      persistCategories(updated);
      return updated;
    });
  }

  // ── Search / Q&A actions ────────────────────────────────────────────────────
  function handleSearchResults(result) {
    setSearchResult(result);
    setIsSearching(true);
  }

  function handleSearchClear() {
    setSearchResult(null);
    setIsSearching(false);
  }

  // ── Delete item ─────────────────────────────────────────────────────────────
  async function handleDelete(id) {
    try {
      await api.deleteItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      if (total !== null) setTotal((t) => t - 1);
      if (selectedItem?.id === id) setSelectedItem(null);
    } catch (err) {
      alert("Could not delete item: " + err.message);
    }
  }

  // ── Item update (from panel tag/category edits) ────────────────────────────
  function handleItemUpdated(updated) {
    setItems((prev) =>
      prev.map((i) => (i.id === updated.id ? { ...i, ...updated } : i)),
    );
    if (selectedItem?.id === updated.id) {
      setSelectedItem((prev) => ({ ...prev, ...updated }));
    }
  }

  // ── Determine displayed items ────────────────────────────────────────────────
  const displayItems =
    isSearching && searchResult?.type === "search"
      ? searchResult.items || []
      : items;

  const showEmpty = !loading && !error && displayItems.length === 0;
  const totalPages = total ? Math.ceil(total / PAGE_SIZE) : 1;

  if (view === "loading") return null;

  if (view === "landing") {
    return (
      <Landing
        onEnterDemo={() => setView("demo")}
        onSignIn={() => setView("login")}
      />
    );
  }

  if (view === "login") {
    return <Login onEnterDemo={() => setView("demo")} />;
  }

  if (view === "demo") return <Demo />;

  return (
    <div className="app-layout">
      <PdfDropZone onSaved={() => loadItems(1, activeCategoryId)} />
      <InstallBanner />
      <TopBar itemCount={isSearching ? null : total} />

      <main className="main-content">
        <CategoryPills
          categories={categories}
          activeId={activeCategoryId}
          onSelect={handleSelectCategory}
          onCreated={handleCategoryCreated}
        />

        <SearchBar
          onResults={handleSearchResults}
          onClear={handleSearchClear}
        />

        {/* Q&A answer box */}
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
                        <a
                          className="source-link"
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
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

        {!loading && !error && displayItems.length > 0 && (
          <div className="item-grid">
            {displayItems.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                categoryName={categoryMap[item.category_id] || null}
                onDelete={handleDelete}
                onClick={() => setSelectedItem(item)}
              />
            ))}
          </div>
        )}

        {showEmpty && <EmptyState searching={isSearching} />}

        {!isSearching && !loading && totalPages > 1 && (
          <div className="pagination">
            <button
              className="page-btn"
              disabled={page <= 1}
              onClick={() => loadItems(page - 1, activeCategoryId)}
            >
              ← Previous
            </button>
            <span className="page-indicator">
              Page {page} of {totalPages}
            </span>
            <button
              className="page-btn"
              disabled={page >= totalPages}
              onClick={() => loadItems(page + 1, activeCategoryId)}
            >
              Next →
            </button>
          </div>
        )}
      </main>

      {selectedItem && (
        <ItemDetailPanel
          item={selectedItem}
          categories={categories}
          onClose={() => setSelectedItem(null)}
          onItemUpdated={handleItemUpdated}
        />
      )}
    </div>
  );
}
