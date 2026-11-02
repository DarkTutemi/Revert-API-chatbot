// Paste in Chrome DevTools Console:
(() => {
  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    const res = await origFetch.apply(this, args);
    if (url.includes('/backend-api/conversation') && args[1]?.method === 'POST' && !url.includes('feedback')) {
      console.log("=== THỰC SỰ GỬI TIN NHẮN TỚI CONVERSATION ===");
      console.log("URL:", url);
      console.log("Tất cả Headers gửi đi:", JSON.stringify(args[1]?.headers, null, 2));
      console.log("Body:", args[1]?.body);
    }
    return res;
  };
  console.log("Hooked conversation message sender!");
})();
