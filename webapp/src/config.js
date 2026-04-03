// Central API URL — override VITE_BACKEND_URL in Vercel env vars for production
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
export default BACKEND_URL;
