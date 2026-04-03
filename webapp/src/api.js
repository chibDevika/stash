/**
 * API client — all fetch calls to the backend go through here.
 * Auth token comes from the active Supabase session (Bearer JWT).
 */

import BACKEND_URL from "./config";
import { supabase } from "./lib/supabase";

const BASE = BACKEND_URL;

async function getAuthHeader() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

async function request(method, path, body) {
  const authHeader = await getAuthHeader();
  const headers = { "Content-Type": "application/json", ...authHeader };

  const opts = { method, headers };
  if (body !== undefined) {
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401) {
      // Token expired or invalid — sign out so the login page is shown
      await supabase.auth.signOut();
    }
    const error = new Error(
      err.detail?.message || err.detail || `Request failed: ${res.status}`,
    );
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

  updateItemTitle: (id, title) =>
    request("PATCH", `/items/${id}/title`, { title }),

  updateItemTags: (id, add = [], remove = []) =>
    request("PATCH", `/items/${id}/tags`, { add, remove }),

  updateItemCategory: (id, categoryId) =>
    request("PATCH", `/items/${id}/category`, { category_id: categoryId }),

  // ── Save ───────────────────────────────────────────────────────────────────
  saveUrl: (url) => request("POST", "/save", { url }),

  uploadPdf: async (file) => {
    const authHeader = await getAuthHeader();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/save/pdf`, {
      method: "POST",
      headers: authHeader,
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      if (res.status === 401) await supabase.auth.signOut();
      const error = new Error(
        err.detail?.message || err.detail || `Request failed: ${res.status}`,
      );
      error.status = res.status;
      error.detail = err.detail;
      throw error;
    }
    return res.json();
  },

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
  queryItem: (id, question) =>
    request("POST", `/query/item/${id}`, { question }),

  // ── Auth / user info ───────────────────────────────────────────────────────
  getMe: () => request("GET", "/auth/me"),

  // ── Admin (requires is_admin in Supabase app_metadata) ────────────────────
  adminListUsers: () => request("GET", "/admin/users"),

  adminCreateUser: (email, password, isAdmin = false) =>
    request("POST", "/admin/users", { email, password, is_admin: isAdmin }),

  // ── Health ─────────────────────────────────────────────────────────────────
  health: () => request("GET", "/health"),

  // ── Demo (no auth required) ────────────────────────────────────────────────
  getDemoItems: () => request("GET", "/demo/items"),
  searchDemo: (q) => request("GET", `/demo/search?q=${encodeURIComponent(q)}`),
  queryDemo: (question) => request("POST", "/demo/query", { question }),
};
