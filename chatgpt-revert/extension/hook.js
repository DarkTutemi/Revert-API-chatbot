// ChatGPT Proxy Bridge - Main World Hook
// Injected at document_start in the MAIN world to intercept conversation responses
(() => {
  if (window.__chatgpt_bridge_hooked) return;
  window.__chatgpt_bridge_hooked = true;

  console.log("%c[ChatGPT Proxy Bridge]%c Main-world fetch interceptor active!", "background: #10a37f; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    const res = await origFetch.apply(this, args);

    const contentType = res.headers.get('content-type') || '';
    // STRICT FILTER: Must be a POST request to conversation endpoint returning text/event-stream
    const isConvStream = url.includes('conversation')
      && contentType.includes('event-stream')
      && args[1]?.method === 'POST';

    if (isConvStream) {
      console.log("%c[ChatGPT Proxy Bridge]%c Intercepted SSE conversation stream!", "color: #10a37f; font-weight: bold;", "", url);
      try {
        const [s1, s2] = res.body.tee();

        (async () => {
          const reader = s2.getReader();
          const decoder = new TextDecoder();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            window.postMessage({ type: "FROM_CHATGPT_HOOK_CHUNK", chunk }, "*");
          }
          window.postMessage({ type: "FROM_CHATGPT_HOOK_DONE" }, "*");
          console.log("%c[ChatGPT Proxy Bridge]%c Stream interception completed!", "color: #10a37f; font-weight: bold;", "");
        })();

        return new Response(s1, {
          status: res.status,
          statusText: res.statusText,
          headers: res.headers
        });
      } catch (err) {
        console.error("[Bridge Hook] Error teeing stream:", err);
      }
    }

    return res;
  };
})();
