// Paste this into DevTools Console on https://chatgpt.com (Profile 16)
// This will intercept the next message sent or simulate sending a message and show the exact headers sent
(() => {
  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    if (url.includes('/backend-api/conversation')) {
      console.log("=== INTERCEPTED CONVERSATION REQUEST ===");
      console.log("URL:", url);
      console.log("Init / Headers:", args[1]);
      if (args[1] && args[1].headers) {
        console.log("Headers detail:", JSON.stringify(args[1].headers, null, 2));
      }
    }
    return origFetch.apply(this, args);
  };
  console.log("--> Hooked /backend-api/conversation! Gửi 1 tin nhắn bất kỳ trên giao diện web để xem headers.");
})();
