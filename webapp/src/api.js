/**
 * API client — all fetch calls to the backend go through here.
 * BACKEND_URL defaults to localhost:8000; override via VITE_BACKEND_URL env var.
 */

import BACKEND_URL, { getApiKey } from "./config";

const BASE = BACKEND_URL;

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const apiKey = getApiKey();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const opts = { method, headers };
  if (body !== undefined) {
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // 401 → fire event so App can show the login prompt
    if (res.status === 401) {
      window.dispatchEvent(new CustomEvent("stash:unauthorized"));
    }
    // Preserve status code on the thrown error so callers can handle 409 etc.
    const error = new Error(err.detail?.message || err.detail || `Request failed: ${res.status}`);
    error.status = res.status;
    error.detail = err.detail;
    throw error;
  }
  return res.json();
}

export const api = {
  // ── Items ──────────────────────────────────────────────────────────────────
  listItems: (page = 1, limit = 20, categoryId = null) => {
    let path = `/items?page=${page}&limit=${limit}`;
    if (categoryId) path += `&category_id=${encodeURIComponent(categoryId)}`;
    return request("GET", path);
  },

  getItem: (id) => request("GET", `/items/${id}`),

  deleteItem: (id) => request("DELETE", `/items/${id}`),

  updateItemTags: (id, add = [], remove = []) =>
    request("PATCH", `/items/${id}/tags`, { add, remove }),

  updateItemCategory: (id, categoryId) =>
    request("PATCH", `/items/${id}/category`, { category_id: categoryId }),

  // ── Save ───────────────────────────────────────────────────────────────────
  saveUrl: (url) => request("POST", "/save", { url }),

  // ── Categories ─────────────────────────────────────────────────────────────
  getCategories: () => request("GET", "/categories"),

  createCategory: (name) => request("POST", "/categories", { name }),

  deleteCategory: (id) => request("DELETE", `/categories/${id}`),

  // ── Search ─────────────────────────────────────────────────────────────────
  search: (q, mode = "hybrid") =>
    request("GET", `/search?q=${encodeURIComponent(q)}&mode=${mode}`),

  // ── RAG Q&A ────────────────────────────────────────────────────────────────
  query: (question) => request("POST", "/query", { question }),

  // ── Per-item chat ──────────────────────────────────────────────────────────
  queryItem: (id, question) => request("POST", `/query/item/${id}`, { question }),

  // ── Health ─────────────────────────────────────────────────────────────────
  health: () => request("GET", "/health"),

  // ── Demo (no auth required) ─────────────────────────────────────────────
  getDemoItems: () => request("GET", "/demo/items"),
  searchDemo: (q) => request("GET", `/demo/search?q=${encodeURIComponent(q)}`),
  queryDemo: (question) => request("POST", "/demo/query", { question }),
};
