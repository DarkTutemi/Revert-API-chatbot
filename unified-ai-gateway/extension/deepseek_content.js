// DeepSeek Content Script (ISOLATED world) for Unified AI Gateway v1.4.0
console.log("%c[Unified Bridge - DeepSeek]%c Content script v1.4.0 (Robust DOM Locator) loaded & active!", "background: #0066ff; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

let activeJobId = null;
let isExecuting = false;
let executionStartTime = 0;
let hookStreamActive = false;

function remoteLog(msg) {
  console.log("[DeepSeek Bridge]", msg);
  try {
    chrome.runtime.sendMessage({ type: "LOG", provider: "deepseek", message: String(msg) });
  } catch (e) {}
}

remoteLog("DeepSeek worker node v1.4.0 active on " + window.location.href);

// Diagnostic scanner
function diagnosePage() {
  try {
    const textareas = Array.from(document.querySelectorAll('textarea'));
    const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'));
    const inputs = Array.from(document.querySelectorAll('input'));
    remoteLog(`[DOM Diagnostic] Textareas: ${textareas.length}, Editables: ${editables.length}, Inputs: ${inputs.length}`);
    textareas.forEach((t, i) => remoteLog(`Textarea[${i}]: id='${t.id}' placeholder='${t.placeholder}' class='${t.className.slice(0, 30)}'`));
    editables.forEach((e, i) => remoteLog(`Editable[${i}]: id='${e.id}' role='${e.getAttribute('role')}' class='${e.className.slice(0, 30)}'`));
  } catch (e) {
    remoteLog("[DOM Diagnostic Error] " + e.message);
  }
}

// Startup scan
setTimeout(diagnosePage, 2500);

window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "FROM_DEEPSEEK_HOOK_CHUNK") {
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
      remoteLog("Stream finished for job " + activeJobId);
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

async function configureMode(modelName) {
  const isReasoning = (modelName || '').toLowerCase().includes('reasoner') || (modelName || '').toLowerCase().includes('r1');
  remoteLog(`Configuring DeepSeek mode: model='${modelName}', isReasoning=${isReasoning}`);

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
      remoteLog("Activating DeepThink (R1) mode...");
      thinkBtn.click();
      await new Promise(r => setTimeout(r, 200));
    } else if (!isReasoning && isAlreadyActive) {
      remoteLog("Deactivating DeepThink mode (switching to V3)...");
      thinkBtn.click();
      await new Promise(r => setTimeout(r, 200));
    }
  }
}

function findInputElement() {
  const el = document.querySelector('textarea#chat-input')
    || document.querySelector('textarea[placeholder*="DeepSeek" i]')
    || document.querySelector('textarea[placeholder*="Ask" i]')
    || document.querySelector('textarea[placeholder*="Message" i]')
    || document.querySelector('textarea[placeholder*="Tin nhắn" i]')
    || document.querySelector('textarea[placeholder*="发消息" i]')
    || document.querySelector('#chat-input')
    || document.querySelector('div[contenteditable="true"]')
    || document.querySelector('div[role="textbox"]')
    || document.querySelector('textarea');
  if (el) return el;

  const iframes = Array.from(document.querySelectorAll('iframe'));
  for (const iframe of iframes) {
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (doc) {
        const iframeInput = doc.querySelector('textarea, div[contenteditable="true"]');
        if (iframeInput) return iframeInput;
      }
    } catch (_) {}
  }
  return null;
}

async function waitForInputElement() {
  for (let i = 0; i < 50; i++) {
    const el = findInputElement();
    if (el) return el;
    if (i % 10 === 0) {
      remoteLog(`Waiting for DeepSeek chat input to mount... (attempt ${i}/50)`);
      diagnosePage();
    }
    await new Promise(r => setTimeout(r, 100));
  }
  return null;
}

function findSendButton(inputEl) {
  let btn = document.querySelector('[aria-label*="Send" i], [aria-label*="发送" i], [aria-label*="Gửi" i]');
  if (btn) return btn;

  const container = inputEl.closest('form')
    || inputEl.parentElement?.parentElement?.parentElement
    || document.body;

  const candidates = Array.from(container.querySelectorAll('button, div[role="button"], [role="button"]'));
  const validButtons = candidates.filter(c => {
    const text = (c.textContent || '').trim().toLowerCase();
    return !(text.includes('deepthink') || text.includes('search') || text.includes('r1') || text.includes('深度') || text.includes('搜索'));
  });

  if (validButtons.length > 0) {
    validButtons.sort((a, b) => {
      const ra = a.getBoundingClientRect();
      const rb = b.getBoundingClientRect();
      return rb.right - ra.right;
    });
    return validButtons[0];
  }

  return document.querySelector('.chat-input-send-button, [class*="send-button"], [class*="sendBtn"]');
}

async function simulateInputAndSend(text, model) {
  await configureMode(model);

  remoteLog("Searching for DeepSeek chat input...");
  const inputEl = await waitForInputElement();

  if (!inputEl) {
    diagnosePage();
    throw new Error("Không tìm thấy ô nhập câu hỏi của DeepSeek sau 5s chờ đợi");
  }

  remoteLog(`Found input: <${inputEl.tagName}> id='${inputEl.id}' placeholder='${inputEl.placeholder || ''}'`);
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

  inputEl.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
  inputEl.dispatchEvent(new Event('input', { bubbles: true }));
  inputEl.dispatchEvent(new Event('change', { bubbles: true }));

  // Wait up to 2.5s for Send button
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

  if (sendBtn) {
    remoteLog("Force-enabling and clicking send button...");
    sendBtn.disabled = false;
    sendBtn.removeAttribute('aria-disabled');
    sendBtn.classList.remove('disabled');
    sendBtn.click();
  }

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

async function observeDomFallback(job_id) {
  remoteLog("DOM fallback observer started for job: " + job_id);
  let accumulated = "";
  let idleCycles = 0;

  for (let i = 0; i < 200; i++) {
    await new Promise(r => setTimeout(r, 300));
    if (activeJobId !== job_id || hookStreamActive) return;

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
        remoteLog("DOM fallback completed! Chars=" + accumulated.length);
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

  remoteLog(`Starting DeepSeek execution for job ${job_id} (model=${model})`);

  try {
    await simulateInputAndSend(prompt_text, model);

    setTimeout(() => {
      if (activeJobId === job_id && !hookStreamActive) {
        observeDomFallback(job_id);
      }
    }, 2000);

    setTimeout(() => {
      if (activeJobId === job_id) {
        remoteLog("Timeout waiting for DeepSeek response: " + job_id);
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
    remoteLog("DeepSeek execution error: " + err.message);
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
        chrome.runtime.sendMessage({ type: "POLL_NOW", provider: "deepseek" }, async (response) => {
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
