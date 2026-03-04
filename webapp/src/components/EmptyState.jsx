import React from "react";

export default function EmptyState({ searching }) {
  if (searching) {
    return (
      <div className="empty-state">
        <div className="empty-title">No results found</div>
        <p className="empty-body">Try different keywords or a broader search.</p>
      </div>
    );
  }

  return (
    <div className="empty-state">
      <div className="empty-icon">📚</div>
      <div className="empty-title">Your Stash is empty</div>
      <p className="empty-body">
        Click the extension on any article or<br />
        YouTube video to save your first item.
      </p>
    </div>
  );
}
