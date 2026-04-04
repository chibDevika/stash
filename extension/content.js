// Runs on the Stash webapp. Reads the Supabase session from localStorage
// and syncs the access token to extension storage so the popup can use it.

function syncSession() {
  const key = Object.keys(localStorage).find(
    (k) => k.startsWith("sb-") && k.endsWith("-auth-token"),
  );
  const raw = key ? localStorage.getItem(key) : null;
  if (raw) {
    try {
      const session = JSON.parse(raw);
      const token = session?.access_token;
      if (token) {
        chrome.storage.local.set({ supabaseToken: token });
        return;
      }
    } catch {}
  }
  chrome.storage.local.remove("supabaseToken");
}

syncSession();
// Re-sync on login/logout
window.addEventListener("storage", syncSession);
