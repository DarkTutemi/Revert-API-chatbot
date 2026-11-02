// Hook both fetch AND XMLHttpRequest (XHR) on ChatGPT web
(() => {
  // 1. Hook fetch
  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] ? args[0].url : '');
    console.log("[FETCH]", args[1]?.method || 'GET', url);
    return origFetch.apply(this, args);
  };

  // 2. Hook XMLHttpRequest
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;
  const origSetHeader = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._url = url;
    this._method = method;
    this._headers = {};
    return origOpen.apply(this, [method, url, ...rest]);
  };

  XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
    if (this._headers) this._headers[header] = value;
    return origSetHeader.apply(this, [header, value]);
  };

  XMLHttpRequest.prototype.send = function(body) {
    console.log("[XHR]", this._method, this._url);
    if (this._url && this._url.includes('conversation')) {
      console.log("=== XHR CONVERSATION CALL ===");
      console.log("Headers:", this._headers);
      console.log("Body:", body);
    }
    return origSend.apply(this, [body]);
  };

  console.log("-> Đã hook cả Fetch và XHR! Gõ tin nhắn và gửi.");
})();
