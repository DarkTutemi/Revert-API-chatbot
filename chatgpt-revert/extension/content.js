// ChatGPT Proxy Bridge - Content Script (runs in ISOLATED world)
console.log("%c[ChatGPT Proxy Bridge]%c Content script loaded & active!", "background: #10a37f; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

let activeJobId = null;
let isExecuting = false;

// Listen to raw SSE chunks intercepted by hook.js
window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "FROM_CHATGPT_HOOK_CHUNK") {
    if (activeJobId) {
      chrome.runtime.sendMessage({
        type: "CHUNK",
        job_id: activeJobId,
        chunk: event.data.chunk
      });
    }
  } else if (event.data?.type === "FROM_CHATGPT_HOOK_DONE") {
    if (activeJobId) {
      chrome.runtime.sendMessage({
        type: "DONE",
        job_id: activeJobId
      });
      activeJobId = null;
      isExecuting = false;
    }
  }
});

async function simulateInputAndSend(text) {
  console.log("%c[ChatGPT Proxy Bridge]%c Injecting prompt into UI:", "color: #0070f3; font-weight: bold;", "", text);

  const inputEl = document.querySelector('#prompt-textarea')
    || document.querySelector('div[contenteditable="true"]')
    || document.querySelector('textarea');

  if (!inputEl) {
    throw new Error("Không tìm thấy khung chat ChatGPT (#prompt-textarea)");
  }

  inputEl.focus();

  // Create active cursor range inside input element for Lexical editor
  try {
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(inputEl);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
  } catch (e) {
    console.warn("[Bridge] Selection setup notice:", e);
  }

  // Native insertText
  try {
    document.execCommand('insertText', false, text);
  } catch (e) {
    if (inputEl.tagName === 'TEXTAREA') {
      inputEl.value = text;
    } else {
      inputEl.innerHTML = `<p>${text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>")}</p>`;
    }
  }

  inputEl.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
  inputEl.dispatchEvent(new Event('input', { bubbles: true }));

  // Wait up to 2 seconds for React to enable the send button
  let sendBtn = null;
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 100));
    sendBtn = document.querySelector('button[data-testid="send-button"]')
      || document.querySelector('button[aria-label="Send prompt"]')
      || document.querySelector('button[aria-label="Gửi lời nhắc"]')
      || document.querySelector('button[aria-label="Gửi tin nhắn"]');

    if (sendBtn && !sendBtn.disabled) {
      console.log("[ChatGPT Proxy Bridge] Clicking send button (attempt " + (i + 1) + ")...");
      sendBtn.click();
      return;
    }
  }

  // Fallback: Form submission or Enter key
  console.log("[ChatGPT Proxy Bridge] Send button fallback: dispatching Enter keydown...");
  const form = inputEl.closest('form');
  if (form && typeof form.requestSubmit === 'function') {
    try {
      form.requestSubmit();
      return;
    } catch (e) {}
  }

  inputEl.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'Enter',
    code: 'Enter',
    keyCode: 13,
    which: 13,
    bubbles: true,
    cancelable: true
  }));
}

async function executeJob(job) {
  const { job_id, prompt_text } = job;
  activeJobId = job_id;
  isExecuting = true;

  try {
    await simulateInputAndSend(prompt_text);

    // Timeout safety: if after 45s no stream finishes, release execution lock
    setTimeout(() => {
      if (activeJobId === job_id) {
        console.warn("[ChatGPT Proxy Bridge] Safety timeout triggered for job:", job_id);
        chrome.runtime.sendMessage({
          type: "ERROR",
          job_id,
          error: "Timeout waiting for ChatGPT response stream"
        });
        activeJobId = null;
        isExecuting = false;
      }
    }, 45000);

  } catch (err) {
    console.error("[ChatGPT Proxy Bridge] Execution error:", err);
    chrome.runtime.sendMessage({
      type: "ERROR",
      job_id,
      error: err.message || String(err)
    });
    activeJobId = null;
    isExecuting = false;
  }
}

// Continuous polling loop
async function pollLoop() {
  while (true) {
    if (!isExecuting) {
      try {
        chrome.runtime.sendMessage({ type: "POLL_NOW" }, async (response) => {
          if (chrome.runtime.lastError) return;
          if (response && response.job && !isExecuting) {
            executeJob(response.job);
          }
        });
      } catch (e) {
        // Silently catch and retry
      }
    }
    await new Promise(r => setTimeout(r, 1000));
  }
}

pollLoop();
