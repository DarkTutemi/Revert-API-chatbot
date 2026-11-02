// Gemini Web Proxy Bridge - Content Script (ISOLATED world) v1.2.0
console.log("%c[Gemini Proxy Bridge]%c Content script v1.2.0 (High-Fidelity Media Capture) loaded & active!", "background: #1a73e8; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;", "");

let activeJobId = null;
let isExecuting = false;
let executionStartTime = 0;

function remoteLog(msg) {
  console.log("[Gemini Bridge]", msg);
  try {
    chrome.runtime.sendMessage({ type: "LOG", message: String(msg) });
  } catch (e) {}
}

remoteLog("Content script v1.2.0 initialized on " + window.location.href);

// Startup diagnostic: scan and report existing images on page
setTimeout(async () => {
  try {
    const allImgs = Array.from(document.querySelectorAll('img'));
    remoteLog(`[Diagnostic] Total <img> elements on page: ${allImgs.length}`);
    const candidates = getCandidateImages();
    remoteLog(`[Diagnostic] Candidate media images on page: ${candidates.length}`);
    for (let i = 0; i < Math.min(candidates.length, 3); i++) {
      const c = candidates[i];
      remoteLog(`[Diagnostic] Media #${i+1}: src=${(c.src || '').slice(0, 50)}... size=${c.naturalWidth}x${c.naturalHeight} alt=${(c.alt || '').slice(0, 30)}`);
    }
  } catch (e) {
    remoteLog(`[Diagnostic] Scan error: ${e.message}`);
  }
}, 2000);

function getAssistantTurns() {
  const models = document.querySelectorAll('model-response');
  if (models.length > 0) return Array.from(models);

  const contents = document.querySelectorAll('message-content');
  if (contents.length > 0) return Array.from(contents);

  return Array.from(document.querySelectorAll('.model-response-text'));
}

// Find candidate images on page (excluding avatars, ui icons, logos)
function getCandidateImages() {
  const allImgs = Array.from(document.querySelectorAll('img'));
  return allImgs.filter(img => {
    const src = img.src || '';
    const alt = (img.alt || '').toLowerCase();
    if (alt.includes('profile') || alt.includes('avatar') || alt.includes('google')) return false;
    if (src.includes('=s32') || src.includes('=s64') || src.includes('=s96') || src.includes('favicon')) return false;
    if (src.includes('gstatic.com/images/branding') || src.includes('googlelogo')) return false;
    if (img.naturalWidth > 0 && img.naturalWidth < 100 && img.naturalHeight < 100) return false;
    return Boolean(src.startsWith('blob:') || src.startsWith('data:image/') || src.includes('googleusercontent.com') || src.includes('lh3.google'));
  });
}

// Extract image data as real Base64 Data URL (data:image/png;base64,...)
async function extractImageAsBase64(imgEl) {
  const src = imgEl.src || '';
  if (!src) return '';
  if (src.startsWith('data:image/')) return src;

  // Wait if image is not yet complete/loaded (up to 4s)
  for (let wait = 0; wait < 16; wait++) {
    if (imgEl.complete && imgEl.naturalWidth > 50) break;
    await new Promise(r => setTimeout(r, 250));
  }

  // Strategy 1: fetch(blobUrl) -> blob -> FileReader -> base64
  // Native in Chrome for same-origin blob: URLs!
  if (src.startsWith('blob:')) {
    try {
      const resp = await fetch(src);
      const blob = await resp.blob();
      const b64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
      if (b64 && b64.startsWith('data:image/')) {
        remoteLog(`Successfully converted blob to base64 (${b64.length} chars)`);
        return b64;
      }
    } catch (e) {
      remoteLog(`fetch(blob) error: ${e.message}, falling back to canvas`);
    }
  }

  // Strategy 2: Canvas drawing
  try {
    const canvas = document.createElement('canvas');
    canvas.width = imgEl.naturalWidth || imgEl.width || 512;
    canvas.height = imgEl.naturalHeight || imgEl.height || 512;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(imgEl, 0, 0);
    const dataUrl = canvas.toDataURL('image/png');
    if (dataUrl && dataUrl.startsWith('data:image/')) {
      remoteLog(`Successfully converted image via canvas (${dataUrl.length} chars)`);
      return dataUrl;
    }
  } catch (e) {
    remoteLog(`Canvas draw error: ${e.message}`);
  }

  // Strategy 3: fetch for https:// URLs
  try {
    const resp = await fetch(src);
    const blob = await resp.blob();
    const b64 = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
    if (b64 && b64.startsWith('data:image/')) {
      return b64;
    }
  } catch (e) {}

  return src;
}

// Find all generated videos on page
function getGeneratedVideosOnPage() {
  const allVideos = Array.from(document.querySelectorAll('video'));
  return allVideos.filter(v => {
    const s = v.src || v.querySelector('source')?.src || '';
    return Boolean(s);
  });
}

// Listen to raw chunks if intercepted by hook.js
window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "FROM_GEMINI_HOOK_CHUNK") {
    if (activeJobId) {
      chrome.runtime.sendMessage({
        type: "CHUNK",
        job_id: activeJobId,
        chunk: event.data.chunk
      });
    }
  } else if (event.data?.type === "FROM_GEMINI_HOOK_DONE") {
    if (activeJobId) {
      remoteLog("Hook done received for job " + activeJobId);
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
  remoteLog("Injecting prompt into Gemini UI: " + text.slice(0, 60));

  const inputEl = document.querySelector('rich-textarea div[contenteditable="true"]')
    || document.querySelector('div[role="textbox"][contenteditable="true"]')
    || document.querySelector('div.ql-editor')
    || document.querySelector('textarea');

  if (!inputEl) {
    remoteLog("ERROR: Input element not found in DOM");
    throw new Error("Không tìm thấy khung nhập văn bản của Gemini");
  }

  remoteLog("Found input element: " + (inputEl.getAttribute('aria-label') || inputEl.className));
  inputEl.focus();

  // Set text inside editor
  try {
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(inputEl);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);
  } catch (e) {
    inputEl.innerHTML = `<p>${text}</p>`;
  }

  if (!inputEl.innerText || !inputEl.innerText.trim()) {
    inputEl.innerHTML = `<p>${text}</p>`;
  }

  // Dispatch events so Angular registers the input
  inputEl.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
  inputEl.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
  inputEl.dispatchEvent(new Event('input', { bubbles: true }));
  inputEl.dispatchEvent(new Event('change', { bubbles: true }));

  // Retry loop: wait up to 3 seconds for send button to become active
  let sendBtn = null;
  for (let attempt = 0; attempt < 30; attempt++) {
    await new Promise(r => setTimeout(r, 100));

    sendBtn = document.querySelector('button[aria-label*="Gửi tin nhắn"]')
      || document.querySelector('button[aria-label*="Send message"]')
      || document.querySelector('button[aria-label*="Gửi"]')
      || document.querySelector('button[aria-label*="Send"]')
      || document.querySelector('button.send-button')
      || document.querySelector('mat-icon[fonticon="send"]')?.closest('button')
      || document.querySelector('span[fonticon="send"]')?.closest('button')
      || document.querySelector('button[jsname="Qx7uuf"]');

    if (sendBtn) {
      const isDisabled = sendBtn.disabled || sendBtn.getAttribute('aria-disabled') === 'true';
      if (!isDisabled) {
        remoteLog("Clicking active send button: " + (sendBtn.getAttribute('aria-label') || 'send button'));
        sendBtn.click();
        return;
      }
    }
  }

  // Force enable if still disabled
  if (sendBtn) {
    remoteLog("Force-enabling and clicking send button...");
    sendBtn.disabled = false;
    sendBtn.removeAttribute('aria-disabled');
    sendBtn.click();
    return;
  }

  remoteLog("Send button fallback: dispatching Enter keydown");
  inputEl.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'Enter',
    code: 'Enter',
    keyCode: 13,
    which: 13,
    bubbles: true
  }));
}

async function observeModelResponse(job_id, prompt_text, initialTurnCount, initialImgSrcs, initialVideoSrcs) {
  const isImagePrompt = /tạo hình|tạo ảnh|vẽ|hình ảnh|bức ảnh|bức tranh|generate image|draw|picture of|photo of|create an image|imagine/i.test(prompt_text);
  remoteLog(`DOM observer v1.2.0 started. Prompt isImage=${isImagePrompt}, initial turns=${initialTurnCount}, initial images=${initialImgSrcs.size}`);

  let accumulated = "";
  let idleCycles = 0;
  let mediaFound = false;
  let seenImgUrls = new Set(initialImgSrcs);
  let seenVideoUrls = new Set(initialVideoSrcs);

  try {
    // Run up to 240 cycles (60 seconds)
    for (let i = 0; i < 240; i++) {
      await new Promise(r => setTimeout(r, 250));
      if (activeJobId !== job_id) break;

      const turns = getAssistantTurns();
      if (turns.length > initialTurnCount) {
        const activeNode = turns[turns.length - 1];
        const turnContainer = activeNode.closest('model-response')
          || activeNode.closest('.conversation-turn')
          || activeNode.parentElement
          || activeNode;

        // 1. Extract clean text from message-content
        let currentText = "";
        const msgContent = activeNode.matches('message-content') ? activeNode : activeNode.querySelector('message-content');
        if (msgContent) {
          currentText = (msgContent.innerText || msgContent.textContent || "").trim();
        } else {
          const clone = activeNode.cloneNode(true);
          const thoughts = clone.querySelectorAll('thought-process, expandable-thought, [class*="thought"]');
          thoughts.forEach(t => t.remove());
          currentText = (clone.innerText || clone.textContent || "").trim();
        }

        // 2. Stream new text delta
        if (currentText.length > accumulated.length) {
          const delta = currentText.slice(accumulated.length);
          accumulated = currentText;
          idleCycles = 0;
          remoteLog("DOM text chunk len=" + delta.length + ": " + delta.slice(0, 40));
          chrome.runtime.sendMessage({
            type: "CHUNK",
            job_id,
            chunk: delta
          });
        } else if (accumulated.length > 0) {
          idleCycles++;
        }

        // 3. Scan for NEW generated images (both inside turn and on whole page)
        const candidates = getCandidateImages();
        const newImgs = candidates.filter(img => img.src && !seenImgUrls.has(img.src));

        if (newImgs.length > 0) {
          for (const targetImg of newImgs) {
            seenImgUrls.add(targetImg.src);
            remoteLog(`Found NEW image element! src=${targetImg.src.slice(0, 40)} size=${targetImg.naturalWidth}x${targetImg.naturalHeight}`);
            
            const b64 = await extractImageAsBase64(targetImg);
            const alt = targetImg.alt || "AI Generated Image";
            const imgMd = `\n\n![${alt}](${b64})\n\n`;
            
            accumulated += imgMd;
            mediaFound = true;
            remoteLog(`Sending image chunk to gateway (data length=${b64.length})`);
            chrome.runtime.sendMessage({
              type: "CHUNK",
              job_id,
              chunk: imgMd
            });
          }
        }

        // 4. Scan for NEW generated videos (Veo)
        const currentVideos = getGeneratedVideosOnPage();
        const newVideos = currentVideos.filter(v => {
          const s = v.src || v.querySelector('source')?.src || '';
          return s && !seenVideoUrls.has(s);
        });

        if (newVideos.length > 0) {
          for (const targetVid of newVideos) {
            const vSrc = targetVid.src || targetVid.querySelector('source')?.src || '';
            seenVideoUrls.add(vSrc);
            remoteLog(`Found NEW video element! src=${vSrc.slice(0, 50)}`);
            const vHtml = `\n\n<video controls autoplay loop style="max-width: 520px; border-radius: 8px; margin: 10px 0;"><source src="${vSrc}" type="video/mp4"></video>\n\n`;
            accumulated += vHtml;
            mediaFound = true;
            chrome.runtime.sendMessage({
              type: "CHUNK",
              job_id,
              chunk: vHtml
            });
          }
        }

        // 5. Completion Check:
        const stopBtn = document.querySelector('button[aria-label*="Dừng"], button[aria-label*="Stop"]');
        const hasActions = activeNode.querySelector('button[aria-label*="Good response"], button[aria-label*="Thích"], button[aria-label*="Sao chép"], button[aria-label*="Copy"]');

        const isStillGeneratingImage = isImagePrompt ||
          /đang tạo hình ảnh|đang vẽ|generating image|đây là hình ảnh|đây là bức ảnh|here is an image/i.test(currentText) ||
          document.querySelector('mat-progress-spinner, [class*="generating"], [class*="loading-indicator"]') !== null;

        // If this is an image request and media hasn't arrived yet, KEEP WAITING! (up to 45s / 180 cycles)
        if (isStillGeneratingImage && !mediaFound && i < 180) {
          if (i % 20 === 0) {
            remoteLog(`Still waiting for Imagen to render image... (cycle ${i}/180, mediaFound=${mediaFound})`);
          }
          continue;
        }

        // Normal text completion or image completed
        if ((!stopBtn || hasActions) && accumulated.length > 0 && idleCycles >= 8) {
          remoteLog(`DOM response complete! Total chars=${accumulated.length}, mediaFound=${mediaFound}`);
          chrome.runtime.sendMessage({
            type: "DONE",
            job_id
          });
          break;
        }
      }
    }
  } catch (err) {
    remoteLog("observeModelResponse error: " + err.message);
  } finally {
    if (activeJobId === job_id) {
      activeJobId = null;
      isExecuting = false;
    }
  }
}

async function executeJob(job) {
  const { job_id, prompt_text } = job;
  activeJobId = job_id;
  isExecuting = true;
  executionStartTime = Date.now();

  remoteLog("Starting execution for job " + job_id);

  try {
    const initialTurnCount = getAssistantTurns().length;
    const initialImgSrcs = new Set(Array.from(document.querySelectorAll('img')).map(img => img.src).filter(Boolean));
    const initialVideoSrcs = new Set(Array.from(document.querySelectorAll('video')).map(v => v.src || v.querySelector('source')?.src).filter(Boolean));

    await simulateInputAndSend(prompt_text);

    // Start DOM stream observer in background
    observeModelResponse(job_id, prompt_text, initialTurnCount, initialImgSrcs, initialVideoSrcs);

    // Safety timeout (90s for image generation)
    setTimeout(() => {
      if (activeJobId === job_id) {
        remoteLog("Safety timeout triggered for job: " + job_id);
        chrome.runtime.sendMessage({
          type: "ERROR",
          job_id,
          error: "Timeout waiting for Gemini response stream"
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
    // Watchdog: If execution has been stuck for > 90 seconds, force-reset it!
    if (isExecuting && Date.now() - executionStartTime > 90000) {
      remoteLog("Watchdog: Forced reset of hung execution lock!");
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
