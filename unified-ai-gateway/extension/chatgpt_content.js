// ChatGPT Content Script (ISOLATED world) for Unified AI Gateway
console.log("%c[Unified Bridge - ChatGPT]%c Content script loaded & active!", "background: #10a37f; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

let activeJobId = null;
let isExecuting = false;
let executionStartTime = 0;

function remoteLog(msg) {
  console.log("[ChatGPT Bridge]", msg);
  try {
    chrome.runtime.sendMessage({ type: "LOG", provider: "chatgpt", message: String(msg) });
  } catch (e) {}
}

remoteLog("ChatGPT worker node active on " + window.location.href);

// Listen to raw SSE chunks from hook.js
window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "FROM_CHATGPT_HOOK_CHUNK") {
    if (activeJobId) {
      chrome.runtime.sendMessage({
        type: "CHUNK",
        job_id: activeJobId,
        chunk: event.data.chunk
      });

      if (typeof event.data.chunk === 'string' && event.data.chunk.includes('[DONE]')) {
        remoteLog("[DONE] frame detected in stream for job " + activeJobId);
        chrome.runtime.sendMessage({
          type: "DONE",
          job_id: activeJobId
        });
        activeJobId = null;
        isExecuting = false;
      }
    }
  } else if (event.data?.type === "FROM_CHATGPT_HOOK_DONE") {
    if (activeJobId) {
      remoteLog("Stream complete for job " + activeJobId);
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
  remoteLog("Injecting prompt into ChatGPT UI: " + text.slice(0, 60));

  const inputEl = document.querySelector('#prompt-textarea')
    || document.querySelector('div[contenteditable="true"]')
    || document.querySelector('textarea');

  if (!inputEl) {
    throw new Error("Không tìm thấy khung chat ChatGPT (#prompt-textarea)");
  }

  inputEl.focus();

  try {
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(inputEl);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
  } catch (e) {}

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

  // Wait for send button
  let sendBtn = null;
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 100));
    sendBtn = document.querySelector('button[data-testid="send-button"]')
      || document.querySelector('button[aria-label="Send prompt"]')
      || document.querySelector('button[aria-label="Gửi lời nhắc"]')
      || document.querySelector('button[aria-label="Send"]')
      || document.querySelector('button[aria-label="Gửi"]');

    if (sendBtn && !sendBtn.disabled && sendBtn.getAttribute('aria-disabled') !== 'true') {
      remoteLog("Clicking active send button");
      sendBtn.click();
      return;
    }
  }

  if (sendBtn) {
    remoteLog("Force clicking send button...");
    sendBtn.disabled = false;
    sendBtn.removeAttribute('aria-disabled');
    sendBtn.click();
    return;
  }

  remoteLog("Fallback: Enter keydown");
  inputEl.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'Enter',
    code: 'Enter',
    keyCode: 13,
    which: 13,
    bubbles: true
  }));
}

async function executeJob(job) {
  const { job_id, prompt_text } = job;
  activeJobId = job_id;
  isExecuting = true;
  executionStartTime = Date.now();

  remoteLog("Starting ChatGPT execution for job " + job_id);

  try {
    await simulateInputAndSend(prompt_text);

    setTimeout(() => {
      if (activeJobId === job_id) {
        remoteLog("Timeout waiting for ChatGPT response: " + job_id);
        chrome.runtime.sendMessage({
          type: "ERROR",
          job_id,
          error: "Timeout waiting for ChatGPT SSE stream"
        });
        activeJobId = null;
        isExecuting = false;
      }
    }, 90000);

  } catch (err) {
    remoteLog("ChatGPT execution error: " + err.message);
    chrome.runtime.sendMessage({
      type: "ERROR",
      job_id,
      error: err.message || String(err)
    });
    activeJobId = null;
    isExecuting = false;
  }
}

async function pollLoop() {
  while (true) {
    if (isExecuting && Date.now() - executionStartTime > 90000) {
      remoteLog("Watchdog: Reset hung execution lock!");
      isExecuting = false;
      activeJobId = null;
    }

    if (!isExecuting) {
      try {
        chrome.runtime.sendMessage({ type: "POLL_NOW", provider: "chatgpt" }, async (response) => {
          if (chrome.runtime.lastError) return;
          if (response && response.job && !isExecuting) {
            executeJob(response.job);
          }
        });
      } catch (e) {}
    }
    await new Promise(r => setTimeout(r, 1000));
  }
}

pollLoop();
