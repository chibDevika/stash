import React, { useState } from "react";
import { api } from "../api";

export default function CategoryPills({ categories, activeId, onSelect, onCreated }) {
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleCreate(e) {
    if (e.key !== "Enter" && e.type !== "blur") return;
    const name = newName.trim();
    if (!name) {
      setAdding(false);
      setNewName("");
      return;
    }
    setCreating(true);
    try {
      const created = await api.createCategory(name);
      onCreated(created);
      setAdding(false);
      setNewName("");
    } catch {
      // Category may already exist — just close the input
      setAdding(false);
      setNewName("");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="category-pills">
      <button
        className={`pill${!activeId ? " active" : ""}`}
        onClick={() => onSelect(null)}
      >
        All
      </button>

      {categories.map((cat) => (
        <button
          key={cat.id}
          className={`pill${activeId === cat.id ? " active" : ""}`}
          onClick={() => onSelect(cat.id)}
        >
          {cat.name}
        </button>
      ))}

      {adding ? (
        <input
          className="pill-add-input"
          autoFocus
          placeholder="Category name…"
          value={newName}
          disabled={creating}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={handleCreate}
          onBlur={handleCreate}
        />
      ) : (
        <button className="pill-add" onClick={() => setAdding(true)}>
          + New category
        </button>
      )}
    </div>
  );
}
