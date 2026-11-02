// Paste this into DevTools Console on https://chatgpt.com (Profile 16)
fetch("/api/auth/session")
  .then(r => r.json())
  .then(data => {
    console.log("=== SESSION DATA ===");
    console.log(JSON.stringify(data));
    console.log("=== ACCESS TOKEN ===");
    console.log(data.accessToken);
  })
  .catch(err => console.error(err));
