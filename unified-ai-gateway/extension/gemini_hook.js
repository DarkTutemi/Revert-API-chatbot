// Gemini Hook (MAIN world) for Unified AI Gateway
(() => {
  if (window.__gemini_proxy_hooked) return;
  window.__gemini_proxy_hooked = true;

  console.log("%c[Unified Bridge - Gemini]%c Interceptor active on gemini.google.com!", "background: #1a73e8; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    const res = await origFetch.apply(this, args);

    const isGeminiStream = url.includes('StreamGenerate') && args[1]?.method === 'POST';
    if (isGeminiStream) {
      console.log("%c[Unified Bridge - Gemini]%c Intercepted StreamGenerate response!", "color: #1a73e8; font-weight: bold;", "", url);
      try {
        const [s1, s2] = res.body.tee();
        (async () => {
          const reader = s2.getReader();
          const decoder = new TextDecoder();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            window.postMessage({ type: "FROM_GEMINI_HOOK_CHUNK", chunk }, "*");
          }
          window.postMessage({ type: "FROM_GEMINI_HOOK_DONE" }, "*");
        })();

        return new Response(s1, {
          status: res.status,
          statusText: res.statusText,
          headers: res.headers
        });
      } catch (err) {
        console.error("[Gemini Hook] Error teeing stream:", err);
      }
    }

    return res;
  };
})();
