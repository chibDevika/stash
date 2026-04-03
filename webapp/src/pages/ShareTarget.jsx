import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BACKEND_URL from "../config";
import { supabase } from "../lib/supabase";

export default function ShareTarget() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("saving"); // saving | saved | duplicate | error

  useEffect(() => {
    const url = searchParams.get("url") || searchParams.get("text");
    const title = searchParams.get("title") || "";

    if (!url) {
      setStatus("error");
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      const headers = { "Content-Type": "application/json" };
      if (session) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      fetch(`${BACKEND_URL}/save`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url, title }),
      })
        .then((res) => {
          if (res.ok) setStatus("saved");
          else if (res.status === 409) setStatus("duplicate");
          else setStatus("error");
        })
        .catch(() => setStatus("error"));
    });
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {status === "saving" && (
          <>
            <div style={styles.spinner} />
            <p style={styles.text}>Saving...</p>
          </>
        )}
        {status === "saved" && (
          <>
            <div style={styles.check}>✓</div>
            <p style={styles.text}>Saved to Stash</p>
            <p style={styles.sub}>You can close this now</p>
          </>
        )}
        {status === "duplicate" && (
          <>
            <div style={styles.check}>✓</div>
            <p style={styles.text}>Already in your Stash</p>
            <p style={styles.sub}>You can close this now</p>
          </>
        )}
        {status === "error" && (
          <>
            <div style={styles.cross}>✕</div>
            <p style={styles.text}>Something went wrong</p>
            <p style={styles.sub}>Check your connection and try again</p>
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#F5F0E8",
  },
  card: {
    background: "#FFFFFF",
    borderRadius: "16px",
    padding: "48px 40px",
    textAlign: "center",
    border: "1px solid #E8E4DD",
    minWidth: "280px",
  },
  check: { fontSize: "48px", color: "#5A8A6A", marginBottom: "16px" },
  cross: { fontSize: "48px", color: "#C4622D", marginBottom: "16px" },
  spinner: {
    width: "36px",
    height: "36px",
    border: "3px solid #E8E4DD",
    borderTop: "3px solid #B85C3A",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    margin: "0 auto 16px",
  },
  text: {
    fontSize: "18px",
    fontWeight: "600",
    color: "#1A1A1A",
    margin: "0 0 8px",
  },
  sub: { fontSize: "14px", color: "#9E968E", margin: 0 },
};
