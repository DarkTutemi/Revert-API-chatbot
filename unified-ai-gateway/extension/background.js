// Unified AI Web Proxy Bridge - Background Service Worker (Port 3000)
console.log("[Unified Bridge] Service worker initialized.");

const GATEWAY_BASE = "http://localhost:3000";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "POLL_NOW") {
    const provider = message.provider || "";
    const url = provider ? `${GATEWAY_BASE}/bridge/poll_now?provider=${encodeURIComponent(provider)}` : `${GATEWAY_BASE}/bridge/poll_now`;
    fetch(url)
      .then(res => res.json())
      .then(data => sendResponse({ job: data && data.job_id ? data : null }))
      .catch(() => sendResponse({ job: null }));
    return true; // Keep channel open for async response
  }

  if (message.type === "LOG") {
    fetch(`${GATEWAY_BASE}/bridge/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message.message, provider: message.provider || "web" })
    }).catch(() => {});
  }

  if (message.type === "CHUNK") {
    fetch(`${GATEWAY_BASE}/bridge/chunk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, chunk: message.chunk })
    }).catch(e => console.error("[Unified SW] Chunk relay error:", e));
  } else if (message.type === "DONE") {
    fetch(`${GATEWAY_BASE}/bridge/done`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id })
    }).catch(e => console.error("[Unified SW] Done relay error:", e));
  } else if (message.type === "ERROR") {
    fetch(`${GATEWAY_BASE}/bridge/error`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, error: message.error })
    }).catch(e => console.error("[Unified SW] Error relay error:", e));
  }
});
