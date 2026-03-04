import React, { useState } from "react";
import { api } from "../api";
import { setApiKey, clearApiKey } from "../config";

export default function Landing({ onEnterDemo, onAuthenticated }) {
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [keyInput, setKeyInput] = useState("");
  const [status, setStatus] = useState("idle"); // idle | connecting | error

  async function handleConnect() {
    setStatus("connecting");
    setApiKey(keyInput.trim());
    try {
      await api.health();
      onAuthenticated();
    } catch (err) {
      clearApiKey();
      setStatus("error");
    }
  }

  return (
    <div className="landing-page">
      <div className="landing-box">
        {/* Logo */}
        <div className="landing-logo">
          <img src="/stash-logo.svg" alt="" className="landing-logo-img" />
          <span className="landing-logo-text">Stash</span>
        </div>

        {/* Headline */}
        <h1 className="landing-headline">Your personal reading memory.</h1>
        <p className="landing-subline">
          Save anything. Recall everything.<br />
          Powered by AI, owned by you.
        </p>

        {/* CTAs */}
        <div className="landing-ctas">
          <button className="landing-btn-primary" onClick={onEnterDemo}>
            Try the demo →
          </button>
          <a
            className="landing-btn-outline"
            href="https://github.com/devikachib/stash"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub →
          </a>
        </div>

        <div className="landing-divider" />

        {/* API key setup */}
        {!showKeyInput ? (
          <p className="landing-already">
            Already have a Stash?{" "}
            <button
              className="landing-key-link"
              onClick={() => setShowKeyInput(true)}
            >
              Enter API key
            </button>
          </p>
        ) : (
          <div className="landing-key-form">
            <input
              className="setup-input"
              type="text"
              placeholder="Your secret key…"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
              autoFocus
            />
            {status === "error" && (
              <p className="setup-error">Invalid key. Try again.</p>
            )}
            <button
              className="setup-btn"
              onClick={handleConnect}
              disabled={status === "connecting" || !keyInput.trim()}
            >
              {status === "connecting" ? "Connecting…" : "Connect"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
