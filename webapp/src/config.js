// Central API URL — override VITE_BACKEND_URL in Vercel env vars for production
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
export default BACKEND_URL;

// API key helpers — stored in localStorage, read on every request
export const getApiKey = () => localStorage.getItem("stash_api_key");
export const setApiKey = (key) => localStorage.setItem("stash_api_key", key);
export const clearApiKey = () => localStorage.removeItem("stash_api_key");
