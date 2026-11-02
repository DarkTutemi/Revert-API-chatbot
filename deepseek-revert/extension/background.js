// DeepSeek Web Proxy Bridge - Service Worker
console.log("[DeepSeek Proxy Bridge] Service worker initialized.");

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "POLL_NOW") {
    fetch("http://localhost:3002/bridge/poll_now")
      .then(res => res.json())
      .then(data => sendResponse({ job: data && data.job_id ? data : null }))
      .catch(() => sendResponse({ job: null }));
    return true; // Keep channel open for async response
  }

  if (message.type === "LOG") {
    fetch("http://localhost:3002/bridge/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message.message })
    }).catch(() => {});
  }

  if (message.type === "CHUNK") {
    fetch("http://localhost:3002/bridge/chunk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, chunk: message.chunk })
    }).catch(e => console.error("[DeepSeek SW] Chunk relay error:", e));
  } else if (message.type === "DONE") {
    fetch("http://localhost:3002/bridge/done", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id })
    }).catch(e => console.error("[DeepSeek SW] Done relay error:", e));
  } else if (message.type === "ERROR") {
    fetch("http://localhost:3002/bridge/error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: message.job_id, error: message.error })
    }).catch(e => console.error("[DeepSeek SW] Error relay error:", e));
  }
});
