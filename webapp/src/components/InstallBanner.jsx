import { useState } from "react";

const DISMISSED_KEY = "stash_install_banner_dismissed";

export default function InstallBanner() {
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches;
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(DISMISSED_KEY) === "1"
  );
  const [showModal, setShowModal] = useState(false);

  if (!isMobile || isStandalone || dismissed) return null;

  function dismiss() {
    localStorage.setItem(DISMISSED_KEY, "1");
    setDismissed(true);
  }

  return (
    <>
      <div className="install-banner">
        <span className="install-banner-text">
          Add Stash to your Home Screen to save from any app.
        </span>
        <button className="install-banner-how" onClick={() => setShowModal(true)}>
          How →
        </button>
        <button className="install-banner-dismiss" onClick={dismiss} aria-label="Dismiss">
          ×
        </button>
      </div>

      {showModal && (
        <div className="install-modal-overlay" onClick={() => setShowModal(false)}>
          <div className="install-modal" onClick={(e) => e.stopPropagation()}>
            <button className="install-modal-close" onClick={() => setShowModal(false)}>×</button>
            <h3 className="install-modal-title">Add to Home Screen</h3>
            <ol className="install-modal-steps">
              <li>Tap the <strong>Share</strong> button in Safari</li>
              <li>Scroll down and tap <strong>"Add to Home Screen"</strong></li>
              <li>Tap <strong>"Add"</strong> — Stash will appear on your home screen</li>
            </ol>
            <p className="install-modal-note">
              Once installed, Stash appears in the share sheet so you can save from any app.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
