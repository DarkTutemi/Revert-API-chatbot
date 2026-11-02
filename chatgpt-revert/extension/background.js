// ChatGPT Proxy Bridge - Service Worker
console.log("[ChatGPT Proxy Bridge] Service worker initialized.");

// Listen to messages from content.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "POLL_NOW") {
    // Non-blocking fetch to local server
    fetch("http://localhost:3000/bridge/poll_now")
      .then(res => res.json())
      .then(data => sendResponse({ job: data && data.job_id ? data : null }))
      .catch(() => sendResponse({ job: null }));
    return true; // Keep sendResponse open for async callback
  }

  if (message.type === "CHUNK") {
    fetch("http://localhost:3000/bridge/chunk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, chunk: message.chunk })
    }).catch(e => console.error("[Bridge SW] Chunk relay error:", e));
  } else if (message.type === "DONE") {
    fetch("http://localhost:3000/bridge/done", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id })
    }).catch(e => console.error("[Bridge SW] Done relay error:", e));
  } else if (message.type === "ERROR") {
    fetch("http://localhost:3000/bridge/error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, error: message.error })
    }).catch(e => console.error("[Bridge SW] Error relay error:", e));
  }
});
