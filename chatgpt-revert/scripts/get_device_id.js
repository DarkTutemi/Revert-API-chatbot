// Run in Chrome DevTools Console on https://chatgpt.com:
(async () => {
  const token = (await (await fetch("/api/auth/session")).json()).accessToken;
  console.log("Device ID cookie:", document.cookie.split(";").find(c => c.trim().startsWith("oai-did=")));
  console.log("All cookies for chatgpt.com:", document.cookie);
})();
