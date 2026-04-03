import React, { useState, useEffect } from "react";
import { supabase } from "../lib/supabase";
import { api } from "../api";

export default function Admin({ onBack }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [createStatus, setCreateStatus] = useState("idle"); // idle | loading | success | error
  const [createError, setCreateError] = useState("");

  async function loadUsers() {
    try {
      const data = await api.adminListUsers();
      setUsers(data);
    } catch (err) {
      setError(err.message || "Could not load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    setCreateStatus("loading");
    setCreateError("");
    try {
      const user = await api.adminCreateUser(
        email.trim(),
        password.trim(),
        isAdmin,
      );
      setUsers((prev) => [...prev, user]);
      setEmail("");
      setPassword("");
      setIsAdmin(false);
      setCreateStatus("success");
      setTimeout(() => setCreateStatus("idle"), 2000);
    } catch (err) {
      setCreateStatus("error");
      setCreateError(err.message || "Could not create user");
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut();
  }

  return (
    <div className="app-layout">
      <header className="topbar">
        <div className="topbar-brand">
          <img src="/stash-logo.svg" alt="" className="topbar-logo-img" />
          <span className="topbar-logo">Stash</span>
        </div>
        <div className="topbar-actions">
          <button className="topbar-btn" onClick={onBack}>
            ← Dashboard
          </button>
          <button className="topbar-btn" onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      </header>

      <main className="main-content" style={{ maxWidth: "700px" }}>
        <h2 style={{ marginBottom: "1.5rem", fontWeight: 600 }}>
          Admin — Users
        </h2>

        {loading ? (
          <div className="page-loading">Loading…</div>
        ) : error ? (
          <p className="page-error">{error}</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Admin</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>{u.is_admin ? "✓" : "—"}</td>
                  <td>
                    {u.created_at
                      ? new Date(u.created_at).toLocaleDateString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h3
          style={{ marginTop: "2rem", marginBottom: "1rem", fontWeight: 600 }}
        >
          Create user
        </h3>
        <form className="admin-form" onSubmit={handleCreate}>
          <input
            className="setup-input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="setup-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <label className="admin-checkbox">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />{" "}
            Grant admin privileges
          </label>
          {createStatus === "error" && (
            <p className="setup-error">{createError}</p>
          )}
          <button
            className="setup-btn"
            type="submit"
            disabled={
              createStatus === "loading" || !email.trim() || !password.trim()
            }
          >
            {createStatus === "loading"
              ? "Creating…"
              : createStatus === "success"
                ? "Created ✓"
                : "Create user"}
          </button>
        </form>
      </main>
    </div>
  );
}
