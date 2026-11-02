// Run in Chrome DevTools Console on https://chatgpt.com:
(() => {
  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    const res = await origFetch.apply(this, args);
    if (url.includes('/backend-api/conversation')) {
      console.log("=== SENT CONVERSATION PAYLOAD & HEADERS ===");
      console.log("URL:", url);
      console.log("Method:", args[1]?.method);
      console.log("Headers:", JSON.stringify(args[1]?.headers, null, 2));
      console.log("Body:", args[1]?.body);
    }
    return res;
  };
  console.log("Hooked conversation full request!");
})();
