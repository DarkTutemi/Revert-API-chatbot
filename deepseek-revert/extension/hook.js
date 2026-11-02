// DeepSeek Web Proxy Bridge - Main World Hook (MAIN world) v1.1.0
(() => {
  if (window.__deepseek_hooked) return;
  window.__deepseek_hooked = true;

  console.log("%c[DeepSeek Proxy Bridge]%c Main world stream hook v1.1.0 installed!", "background: #0066ff; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    
    // Debug log all chat API calls
    if (url.includes('/api/') || url.includes('chat')) {
      window.postMessage({ type: "FROM_DEEPSEEK_HOOK_URL", url }, "*");
    }

    const res = await origFetch.apply(this, args);

    // Match DeepSeek chat completion endpoint
    if (url.includes('/chat/completion') || url.includes('/completion') || url.includes('chat_session')) {
      console.log("[DeepSeek Hook] Detected chat stream:", url);
      try {
        const [s1, s2] = res.body.tee();
        (async () => {
          const reader = s2.getReader();
          const decoder = new TextDecoder();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            window.postMessage({ type: "FROM_DEEPSEEK_HOOK_CHUNK", chunk }, "*");
          }
          console.log("[DeepSeek Hook] Stream finished.");
          window.postMessage({ type: "FROM_DEEPSEEK_HOOK_DONE" }, "*");
        })();

        return new Response(s1, {
          status: res.status,
          statusText: res.statusText,
          headers: res.headers
        });
      } catch (e) {
        console.error("[DeepSeek Hook] Stream tee error:", e);
      }
    }

    return res;
  };
})();
