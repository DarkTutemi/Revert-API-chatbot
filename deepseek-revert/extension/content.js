// DeepSeek Web Proxy Bridge - Content Script (ISOLATED world) v1.3.0
console.log("%c[DeepSeek Proxy Bridge]%c Content script v1.3.0 (Reliable Relay) loaded & active!", "background: #0066ff; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

let activeJobId = null;
let isExecuting = false;
let executionStartTime = 0;
let hookStreamActive = false;

function remoteLog(msg) {
  console.log("[DeepSeek Bridge]", msg);
  try {
    chrome.runtime.sendMessage({ type: "LOG", message: String(msg) });
  } catch (e) {}
}

remoteLog("Content script v1.3.0 initialized on " + window.location.href);

// Startup Diagnostic Scan
setTimeout(() => {
  try {
    const input = findInputElement();
    if (input) {
      remoteLog(`[Startup Diagnostic] Input: tag=${input.tagName} id=${input.id} class='${input.className}'`);
      dumpInputArea(input);
    } else {
      remoteLog("[Startup Diagnostic] Input element not found yet on page");
    }
  } catch (e) {
    remoteLog("[Startup Diagnostic Error] " + e.message);
  }
}, 2000);

function dumpInputArea(inputEl) {
  try {
    const container = inputEl.closest('form')
      || inputEl.parentElement?.parentElement?.parentElement
      || document.body;

    const allBtns = Array.from(container.querySelectorAll('button, div[role="button"], [role="button"]'));
    remoteLog(`[Diagnostic] Container has ${allBtns.length} clickable elements`);
    allBtns.forEach((b, idx) => {
      const aria = b.getAttribute('aria-label') || '';
      const cls = b.className || '';
      const text = (b.innerText || '').slice(0, 20);
      remoteLog(`Btn[${idx}]: tag=${b.tagName} aria='${aria}' class='${cls}' text='${text}'`);
    });
  } catch (e) {}
}

// Listen to stream messages from hook.js
window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "FROM_DEEPSEEK_HOOK_URL") {
    remoteLog("[Network Hook] Captured URL: " + event.data.url);
  } else if (event.data?.type === "FROM_DEEPSEEK_HOOK_CHUNK") {
    hookStreamActive = true;
    if (activeJobId) {
      chrome.runtime.sendMessage({
        type: "CHUNK",
        job_id: activeJobId,
        chunk: event.data.chunk
      });
    }
  } else if (event.data?.type === "FROM_DEEPSEEK_HOOK_DONE") {
    if (activeJobId) {
      remoteLog("Hook stream completed for job " + activeJobId);
      chrome.runtime.sendMessage({
        type: "DONE",
        job_id: activeJobId
      });
      activeJobId = null;
      isExecuting = false;
      hookStreamActive = false;
    }
  }
});

// Configure DeepThink (R1) mode toggle
async function configureMode(modelName) {
  const isReasoning = (modelName || '').toLowerCase().includes('reasoner') || (modelName || '').toLowerCase().includes('r1');
  remoteLog(`Configuring mode for model '${modelName}' (isReasoning=${isReasoning})`);

  const buttons = Array.from(document.querySelectorAll('button, div[role="button"], span'));
  const thinkBtn = buttons.find(b => {
    const t = (b.textContent || '').trim().toLowerCase();
    const aria = (b.getAttribute('aria-label') || '').toLowerCase();
    return t.includes('deepthink') || t.includes('r1') || t.includes('深度思考') || aria.includes('deepthink') || aria.includes('r1');
  });

  if (thinkBtn) {
    const isAlreadyActive = thinkBtn.classList.contains('active') ||
      thinkBtn.getAttribute('aria-pressed') === 'true' ||
      thinkBtn.getAttribute('data-active') === 'true' ||
      thinkBtn.closest('.active') !== null;

    if (isReasoning && !isAlreadyActive) {
      remoteLog("Enabling DeepThink (R1) mode...");
      thinkBtn.click();
      await new Promise(r => setTimeout(r, 200));
    } else if (!isReasoning && isAlreadyActive) {
      remoteLog("Disabling DeepThink mode (switching to V3)...");
      thinkBtn.click();
      await new Promise(r => setTimeout(r, 200));
    }
  }
}

// Find input element (textarea or contenteditable)
function findInputElement() {
  return document.querySelector('textarea#chat-input')
    || document.querySelector('textarea[placeholder*="DeepSeek"]')
    || document.querySelector('textarea[placeholder*="Ask"]')
    || document.querySelector('textarea[placeholder*="发消息"]')
    || document.querySelector('div[contenteditable="true"]')
    || document.querySelector('textarea');
}

// Find send button element using geometry and attributes
function findSendButton(inputEl) {
  // 1. By aria-label
  let btn = document.querySelector('[aria-label*="Send" i], [aria-label*="发送" i], [aria-label*="Gửi" i]');
  if (btn) return btn;

  // 2. Search container for the rightmost bottom button (standard send button position)
  const container = inputEl.closest('form')
    || inputEl.parentElement?.parentElement?.parentElement
    || document.body;

  const candidates = Array.from(container.querySelectorAll('button, div[role="button"], [role="button"]'));
  const validButtons = candidates.filter(c => {
    const text = (c.textContent || '').trim().toLowerCase();
    // Exclude mode toggles
    return !(text.includes('deepthink') || text.includes('search') || text.includes('r1') || text.includes('深度') || text.includes('搜索'));
  });

  if (validButtons.length > 0) {
    // Sort by right position descending (rightmost element is the send button)
    validButtons.sort((a, b) => {
      const ra = a.getBoundingClientRect();
      const rb = b.getBoundingClientRect();
      return rb.right - ra.right;
    });
    return validButtons[0];
  }

  return document.querySelector('.chat-input-send-button, [class*="send-button"], [class*="sendBtn"]');
}

// Simulate input injection into DeepSeek UI
async function simulateInputAndSend(text, model) {
  await configureMode(model);

  remoteLog("Injecting prompt into DeepSeek UI: " + text.slice(0, 60));
  const inputEl = findInputElement();

  if (!inputEl) {
    remoteLog("ERROR: Input element not found in DOM");
    throw new Error("Không tìm thấy ô nhập câu hỏi của DeepSeek");
  }

  inputEl.focus();

  // Strategy 1: React native value setter
  try {
    const prototype = Object.getPrototypeOf(inputEl);
    const nativeSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set
      || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
    if (nativeSetter && inputEl.tagName === 'TEXTAREA') {
      nativeSetter.call(inputEl, text);
    } else {
      inputEl.value = text;
    }
  } catch (e) {
    inputEl.value = text;
  }

  // Strategy 2: execCommand insertText
  try {
    inputEl.select();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);
  } catch (e) {}

  if (!inputEl.value && (!inputEl.innerText || !inputEl.innerText.trim())) {
    inputEl.innerHTML = text;
  }

  // Dispatch all React/Vue input events
  inputEl.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
  inputEl.dispatchEvent(new Event('input', { bubbles: true }));
  inputEl.dispatchEvent(new Event('change', { bubbles: true }));

  // Wait up to 2.5s for Send button to activate
  let sendBtn = null;
  for (let attempt = 0; attempt < 25; attempt++) {
    await new Promise(r => setTimeout(r, 100));

    sendBtn = findSendButton(inputEl);
    if (sendBtn) {
      const isDisabled = sendBtn.disabled || sendBtn.getAttribute('aria-disabled') === 'true' || sendBtn.classList.contains('disabled');
      if (!isDisabled) {
        remoteLog("Clicking active send button: " + (sendBtn.getAttribute('aria-label') || sendBtn.className || 'button'));
        sendBtn.click();
        return;
      }
    }
  }

  // Force enable and click
  if (sendBtn) {
    remoteLog("Force-enabling and clicking send button...");
    sendBtn.disabled = false;
    sendBtn.removeAttribute('aria-disabled');
    sendBtn.classList.remove('disabled');
    sendBtn.click();
  }

  // Always also dispatch Enter keydown
  remoteLog("Dispatching Enter keydown...");
  const enterEvent = new KeyboardEvent('keydown', {
    key: 'Enter',
    code: 'Enter',
    keyCode: 13,
    which: 13,
    bubbles: true,
    cancelable: true
  });
  inputEl.dispatchEvent(enterEvent);
}

// Fallback DOM Observer
async function observeDomFallback(job_id) {
  remoteLog("DOM fallback observer started for job: " + job_id);
  let accumulated = "";
  let idleCycles = 0;

  for (let i = 0; i < 200; i++) {
    await new Promise(r => setTimeout(r, 300));
    if (activeJobId !== job_id || hookStreamActive) {
      remoteLog("Hook stream is active or job finished, exiting DOM fallback.");
      return;
    }

    const assistantTurns = document.querySelectorAll('.chat-message-assistant, .ds-markdown, [class*="assistant-message"]');
    if (assistantTurns.length > 0) {
      const latestTurn = assistantTurns[assistantTurns.length - 1];
      const text = (latestTurn.innerText || latestTurn.textContent || "").trim();

      if (text.length > accumulated.length) {
        const delta = text.slice(accumulated.length);
        accumulated = text;
        idleCycles = 0;
        chrome.runtime.sendMessage({
          type: "CHUNK",
          job_id,
          chunk: delta
        });
      } else if (accumulated.length > 0) {
        idleCycles++;
      }

      const stopBtn = document.querySelector('div[role="button"][aria-label*="Stop"], button[aria-label*="Stop"], [class*="stop"]');
      if (!stopBtn && accumulated.length > 0 && idleCycles >= 8) {
        remoteLog("DOM fallback detected completion! Total chars=" + accumulated.length);
        chrome.runtime.sendMessage({
          type: "DONE",
          job_id
        });
        activeJobId = null;
        isExecuting = false;
        break;
      }
    }
  }
}

async function executeJob(job) {
  const { job_id, prompt_text, model } = job;
  activeJobId = job_id;
  isExecuting = true;
  hookStreamActive = false;
  executionStartTime = Date.now();

  remoteLog(`Starting execution for job ${job_id} with model ${model}`);

  try {
    await simulateInputAndSend(prompt_text, model);

    // Give fetch hook 2 seconds to fire; if not, fallback to DOM observer
    setTimeout(() => {
      if (activeJobId === job_id && !hookStreamActive) {
        observeDomFallback(job_id);
      }
    }, 2000);

    // 90s safety timeout
    setTimeout(() => {
      if (activeJobId === job_id) {
        remoteLog("Safety timeout triggered for job: " + job_id);
        chrome.runtime.sendMessage({
          type: "ERROR",
          job_id,
          error: "Timeout waiting for DeepSeek response"
        });
        activeJobId = null;
        isExecuting = false;
      }
    }, 90000);

  } catch (err) {
    remoteLog("Execution error: " + err.message);
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
      remoteLog("Watchdog: Reset stuck execution lock!");
      isExecuting = false;
      activeJobId = null;
    }

    if (!isExecuting) {
      try {
        chrome.runtime.sendMessage({ type: "POLL_NOW" }, async (response) => {
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
