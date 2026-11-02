// Run in Chrome DevTools Console on https://chatgpt.com:
(async () => {
  const r = await fetch("https://chatgpt.com/backend-api/sentinel/chat-requirements", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "OAI-Device-Id": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3"
    },
    body: JSON.stringify({})
  });
  const data = await r.json();
  console.log("=== CHAT REQUIREMENTS IN CHROME ===");
  console.log("turnstile required:", data.turnstile?.required);
  console.log("proofofwork required:", data.proofofwork?.required);
  console.log("full data:", JSON.stringify(data));
})();
