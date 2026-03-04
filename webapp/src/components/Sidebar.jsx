import React from "react";
import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">Stash</div>
      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          All items
        </NavLink>
        <NavLink
          to="/ask"
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          Ask a question
        </NavLink>
      </nav>
    </aside>
  );
}
