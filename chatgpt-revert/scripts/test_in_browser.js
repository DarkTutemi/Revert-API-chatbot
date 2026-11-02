// Run this in Chrome DevTools Console on https://chatgpt.com:
(async () => {
  console.log("Cookies:", document.cookie);
  const r = await fetch("https://chatgpt.com/backend-api/sentinel/chat-requirements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
  const data = await r.json();
  console.log("Chat requirements from browser:", data);
})();
