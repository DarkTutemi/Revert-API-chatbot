// Paste this into DevTools Console on https://chatgpt.com (Profile 16):
(async () => {
  const token = (await (await fetch("/api/auth/session")).json()).accessToken;
  console.log("Token:", token.slice(0, 30));
  
  // Call init
  const initRes = await fetch("/backend-api/conversation/init", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      "OAI-Language": "vi-VN"
    },
    body: JSON.stringify({})
  });
  console.log("Init status in browser:", initRes.status);
})();
