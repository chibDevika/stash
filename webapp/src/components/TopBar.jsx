import React from "react";

export default function TopBar({ itemCount }) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <img src="/stash-logo.svg" alt="" className="topbar-logo-img" />
        <span className="topbar-logo">Stash</span>
      </div>
      {itemCount != null && (
        <span className="topbar-count">{itemCount} item{itemCount !== 1 ? "s" : ""}</span>
      )}
    </header>
  );
}
