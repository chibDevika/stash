// Options page: lets the user configure backend URL, dashboard URL, and API key.
// Stored in chrome.storage.sync so popup.js can read them.

const backendInput = document.getElementById("backend-url");
const frontendInput = document.getElementById("frontend-url");
const apiKeyInput = document.getElementById("api-key");
const saveBtn = document.getElementById("save-btn");
const savedMsg = document.getElementById("saved-msg");

// Load saved values on page open
chrome.storage.sync.get(["backendUrl", "frontendUrl", "apiKey"], (result) => {
  backendInput.value = result.backendUrl || "http://localhost:8000";
  frontendInput.value = result.frontendUrl || "http://localhost:3000";
  apiKeyInput.value = result.apiKey || "";
});

saveBtn.addEventListener("click", () => {
  const backendUrl = backendInput.value.trim().replace(/\/$/, ""); // strip trailing slash
  const frontendUrl = frontendInput.value.trim().replace(/\/$/, "");
  const apiKey = apiKeyInput.value.trim();

  chrome.storage.sync.set({ backendUrl, frontendUrl, apiKey }, () => {
    savedMsg.style.display = "block";
    setTimeout(() => { savedMsg.style.display = "none"; }, 2000);
  });
});
