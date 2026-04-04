import React from "react";
import { supabase } from "../lib/supabase";

async function signInWithGoogle() {
  await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
}

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

        {/* Google sign-in */}
        <button className="google-btn" onClick={signInWithGoogle}>
          <GoogleIcon />
          Continue with Google
        </button>

        <div className="landing-divider" />

        <p className="landing-already">
          Already have an account?{" "}
          <button className="landing-key-link" onClick={onSignIn}>
            Sign in with email →
          </button>
        </p>

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

function GoogleIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z"
        fill="#EA4335"
      />
    </svg>
  );
}
