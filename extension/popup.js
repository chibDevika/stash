// Stash extension popup logic
// Fire-and-forget save: returns immediately with status='pending'.
// Shows "Saved!" on 200, "Already in your Stash" on 409.

const DEFAULT_BACKEND_URL = "http://localhost:8000";
const DEFAULT_FRONTEND_URL = "http://localhost:3000";

const states = {
  idle: document.getElementById("state-idle"),
  saving: document.getElementById("state-saving"),
  saved: document.getElementById("state-saved"),
  duplicate: document.getElementById("state-duplicate"),
  error: document.getElementById("state-error"),
};

function showState(name) {
  Object.entries(states).forEach(([key, el]) => {
    el.classList.toggle("hidden", key !== name);
  });
}

// Pre-fill title input with current page title
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  if (tab) {
    document.getElementById("page-title").value = tab.title || tab.url;
  }
});

// Dashboard links — read frontendUrl from storage
async function openDashboard() {
  const { frontendUrl } = await chrome.storage.sync.get(["frontendUrl"]);
  chrome.tabs.create({ url: frontendUrl || DEFAULT_FRONTEND_URL });
}
document.getElementById("open-dashboard").addEventListener("click", (e) => {
  e.preventDefault();
  openDashboard();
});
document.getElementById("open-dashboard-dup").addEventListener("click", (e) => {
  e.preventDefault();
  openDashboard();
});

// Read the Supabase session token — first from cache, then by injecting into
// any open Stash tab, so the popup works even if the content script hasn't run.
async function getSupabaseToken(backendUrl) {
  // 1. Try the cached token from the content script
  const { supabaseToken } = await chrome.storage.local.get(["supabaseToken"]);
  if (supabaseToken) return supabaseToken;

  // 2. Find an open Stash tab and read localStorage directly
  const { frontendUrl } = await chrome.storage.sync.get(["frontendUrl"]);
  const base = (frontendUrl || DEFAULT_FRONTEND_URL).replace(/\/$/, "");
  const tabs = await chrome.tabs.query({ url: base + "/*" });
  if (!tabs.length) return null;

  const results = await chrome.scripting.executeScript({
    target: { tabId: tabs[0].id },
    func: () => {
      const key = Object.keys(localStorage).find(
        (k) => k.startsWith("sb-") && k.endsWith("-auth-token"),
      );
      if (!key) return null;
      try {
        const session = JSON.parse(localStorage.getItem(key));
        return session?.access_token || null;
      } catch {
        return null;
      }
    },
  });

  const token = results?.[0]?.result || null;
  if (token) chrome.storage.local.set({ supabaseToken: token });
  return token;
}

// Save button + retry
document.getElementById("save-btn").addEventListener("click", saveCurrentPage);
document.getElementById("retry-btn").addEventListener("click", saveCurrentPage);

async function saveCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) {
    showError("Could not get the current page URL.");
    return;
  }

  if (
    tab.url.startsWith("chrome://") ||
    tab.url.startsWith("chrome-extension://")
  ) {
    showError(
      "Can't save browser pages. Navigate to an article or YouTube video first.",
    );
    return;
  }

  showState("saving");

  const { backendUrl } = await chrome.storage.sync.get(["backendUrl"]);
  const apiBase = backendUrl || DEFAULT_BACKEND_URL;

  const token = await getSupabaseToken(backendUrl);
  if (!token) {
    showError("Not signed in. Open the Stash dashboard and sign in first.");
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  try {
    const customTitle = document.getElementById("page-title").value.trim();
    const response = await fetch(`${apiBase}/save`, {
      method: "POST",
      headers,
      body: JSON.stringify({ url: tab.url, title: customTitle || undefined }),
    });

    if (response.status === 409) {
      // Already saved
      showState("duplicate");
      return;
    }

    if (response.status === 401) {
      showError("Session expired. Open the Stash dashboard and sign in again.");
      return;
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Server returned ${response.status}`);
    }

    // 200 — saved successfully (status='pending', AI runs in background)
    showState("saved");
  } catch (err) {
    if (
      err.message.includes("Failed to fetch") ||
      err.message.includes("NetworkError")
    ) {
      showError(
        `Could not connect to the backend at ${apiBase}.\n` +
          "Make sure Docker is running: docker-compose up",
      );
    } else {
      showError(err.message || "Something went wrong. Please try again.");
    }
  }
}

function showError(message) {
  showState("error");
  document.getElementById("error-message").textContent = message;
}
