import React, { useState } from "react";
import { supabase } from "../lib/supabase";

export default function Login({ onEnterDemo }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSignIn(e) {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) {
      setStatus("error");
      setErrorMsg(error.message);
    }
    // On success, onAuthStateChange in App.jsx fires and switches to dashboard
  }

  return (
    <div className="landing-page">
      <div className="landing-box">
        <div className="landing-logo">
          <img src="/stash-logo.svg" alt="" className="landing-logo-img" />
          <span className="landing-logo-text">Stash</span>
        </div>

        <h1 className="landing-headline">Sign in to your Stash</h1>
        <p className="landing-subline">Your personal reading memory.</p>

        <form className="login-form" onSubmit={handleSignIn}>
          <input
            className="setup-input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <input
            className="setup-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {status === "error" && <p className="setup-error">{errorMsg}</p>}
          <button
            className="setup-btn"
            type="submit"
            disabled={status === "loading"}
          >
            {status === "loading" ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="landing-divider" />

        <p className="landing-already">
          Just browsing?{" "}
          <button className="landing-key-link" onClick={onEnterDemo}>
            Try the demo →
          </button>
        </p>
      </div>
    </div>
  );
}
