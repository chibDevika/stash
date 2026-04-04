import React from "react";

export default function Landing({ onEnterDemo, onSignIn }) {
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
          Save anything. Recall everything.
          <br />
          Powered by AI, owned by you.
        </p>

        {/* CTAs */}
        <div className="landing-ctas">
          <button className="landing-btn-primary" onClick={onEnterDemo}>
            Try the demo →
          </button>
          <a
            className="landing-btn-outline"
            href="https://github.com/chibDevika/stash"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub →
          </a>
        </div>

        <div className="landing-divider" />

        <p className="landing-already">
          Have an account?{" "}
          <button className="landing-key-link" onClick={onSignIn}>
            Sign in →
          </button>
        </p>
      </div>
    </div>
  );
}
