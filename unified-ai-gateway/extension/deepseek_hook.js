// DeepSeek Hook (MAIN world) for Unified AI Gateway
(() => {
  if (window.__deepseek_hooked) return;
  window.__deepseek_hooked = true;

  console.log("%c[Unified Bridge - DeepSeek]%c Interceptor active on deepseek.com!", "background: #0066ff; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    const res = await origFetch.apply(this, args);

    if (url.includes('/chat/completion') || url.includes('/completion') || url.includes('chat_session')) {
      console.log("%c[Unified Bridge - DeepSeek]%c Intercepted chat stream:", "color: #0066ff; font-weight: bold;", "", url);
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
