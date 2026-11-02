# CẨM NANG ĐẢO NGƯỢC & PROXY HÓA CÁC NỀN TẢNG AI WEB (CHATGPT, GEMINI, DEEPSEEK, CLAUDE)
> **Tác giả:** spinach & paneer  
> **Phiên bản:** 2.0.0 (Cập nhật Tháng 11/2026)  
> **Mục tiêu:** Xây dựng hệ thống Reverse Proxy chuẩn OpenAI API từ Web UI của các nền tảng AI lớn (ChatGPT, Google Gemini, DeepSeek, Claude Web) với khả năng vượt qua 100% rào cản chống bot, Cloudflare WAF, Turnstile, PoW, Google Batchexecute, App-Bound Encryption và CSP.

---

## 1. Bản Đồ Thách Thức Kỹ Thuật (Modern Anti-Bot Landscape)

Khi trích xuất API từ các nền tảng Web AI hiện đại, các phương pháp tự động hóa truyền thống (Headless Selenium, Puppeteer thuần, `curl_cffi` gửi request độc lập) đều thất bại vì 5 phòng tuyến:

| Phòng tuyến | Cơ chế bảo vệ | Điểm gãy của phương pháp cũ |
| :--- | :--- | :--- |
| **Cloudflare WAF & Turnstile** | TLS Fingerprint (JA3/JA4), HTTP/2 frame fingerprinting, IP reputation, Turnstile challenges. | Các thư viện HTTP thông thường bị phát hiện fingerprint hoặc bắt captcha Turnstile ngay lập tức. |
| **Dynamic VM Token & PoW** | OpenAI Sentinel (PoW SHA3 + Turnstile + Conduit), Google SNlM0e (`at` token) + Batchexecute RPC, DeepSeek Proof-of-Work. | Token được sinh ra bởi máy ảo VM JavaScript / WebAssembly chạy ngầm trong trình duyệt. Không thể tự tính toán độc lập ngoài Python. |
| **Windows App-Bound Encryption** | Chrome 127+ mã hóa cookie bằng dịch vụ hệ thống `v20`, khóa cứng theo danh tính tiến trình Chrome. | Script ngoài không thể đọc trực tiếp file SQLite `Network\Cookies` để lấy cookie session. |
| **Content Security Policy (CSP)** | `connect-src 'self' ...` trên domain `chatgpt.com`, `gemini.google.com`, `chat.deepseek.com`. | DevTools Console script không thể gọi `fetch("http://localhost:3000")` để chuyển dữ liệu ra ngoài. |
| **Origin Isolation đối với Media** | Imagen / DALL-E / Veo sinh ảnh/video dưới dạng `blob:https://...` lưu trong RAM trình duyệt. | Tiến trình ngoài không thể tải các URL `blob:` này vì giới hạn Same-Origin Policy. |

---

## 2. Kiến Trúc "In-Browser Bridge & Extension Hook" (Giải Pháp Bất Khả Chiến Bại)

Thay vì cố gắng giả lập trình duyệt ngoài môi trường thật, giải pháp tối thượng là: **Biến chính trình duyệt Chrome thật của người dùng thành một Worker Node** thông qua một Manifest V3 Chrome Extension siêu nhẹ.

```
[ Khách hàng / IDE / PySide6 GUI / MCP Client ]
         │ (OpenAI format: /v1/chat/completions)
         ▼
[ Python Local Server :3000 / :3001 / :3002 ] ─── (Active Polling: /bridge/poll_now) ───┐
         ▲                                                                               │
         │ (SSE Chunks & Base64 Media Relay: /bridge/chunk)                              │
         │                                                                               │
┌────────┴───────────────────────────────────────────────────────────────────────────────┴────────┐
│                        CHROME BROWSER (Profile Thật Đã Đăng Nhập)                              │
│                                                                                                │
│  [ Extension Service Worker: background.js ] (Bypass CSP, Điều phối Jobs, Heartbeat)           │
│         │                                                                                      │
│         ▼                                                                                      │
│  [ Extension Content Script: content.js ] (ISOLATED World - Quét DOM, State, Media Blob)       │
│         │                                                                                      │
│         │ (window.postMessage)                                                                 │
│         ▼                                                                                      │
│  [ Main World Hook: hook.js ] (MAIN World - Gắn vào window.fetch / XHR Stream Interception)   │
│         │                                                                                      │
│         ▼                                                                                      │
│  [ Web AI Core: chatgpt.com / gemini.google.com / chat.deepseek.com ] (Zero 403 / Zero Ban)    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Các nguyên tắc sống còn khi thiết kế Extension Bridge:

1. **Active Polling từ Tab (`content.js`), không dùng `background.js` làm vòng lặp:**
   - Manifest V3 tự động "ngủ đông" (Inactive) Service Worker sau 30 giây rảnh rỗi.
   - Tab trình duyệt mở thật sự không bao giờ bị tắt. `content.js` dùng `setInterval(1000)` gọi `chrome.runtime.sendMessage` sẽ đánh thức Service Worker dậy tức thì.
2. **Tách biệt 2 tầng World:**
   - `world: "MAIN"` (`hook.js`): Chạy chung ngữ cảnh với JavaScript của trang để bọc `window.fetch` / `XMLHttpRequest`, trích xuất trực tiếp luồng stream.
   - `world: "ISOLATED"` (`content.js`): Có quyền gọi Chrome API (`chrome.runtime`), giao tiếp với `hook.js` qua `window.postMessage`.
3. **Mô phỏng thao tác gửi chuẩn Editor (Angular / React / Lexical):**
   - Với rich text editors: Không gán `.value` thô. Tạo con trỏ `Selection` ảo và dùng `document.execCommand('insertText')`, dispatch `beforeinput` + `input`.
   - **Click Trigger thay vì Synthetic KeyboardEvent:** Các framework hiện đại (như Angular của Google) kiểm tra `event.isTrusted === true`. Synthetic Enter keydown sẽ bị bỏ qua. Phải dùng polling loop chờ nút Send sáng hoặc cưỡng chế xóa thuộc tính `disabled`/`aria-disabled` rồi gọi trực tiếp `.click()`.
4. **Giải pháp trích xuất Media Blob (`blob:` sang Base64):**
   - Sử dụng `fetch(blobUrl) -> blob -> FileReader.readAsDataURL` ngay trong nội hàm content script để chuyển đổi ảnh/video blob thành chuỗi `data:image/png;base64,...` hoặc `data:video/mp4;base64,...`. Tránh hoàn toàn lỗi `Canvas Tainted SecurityError`.
5. **Image Job Watchdog (Tránh hoàn thành sớm):**
   - Khi tạo hình ảnh, Gemini/ChatGPT phản hồi text trước ("Đây là hình ảnh..."), sau đó 15–25 giây mới nhúng thẻ `<img>` hoàn chỉnh.
   - Observer phải nhận diện câu lệnh tạo ảnh và **giữ kết nối (không gửi `DONE`)** cho đến khi thẻ `<img>` xuất hiện thực sự trên DOM.

---

## 3. Dự Án Đã Triển Khai Hoàn Tất

### 3.1. ChatGPT Gateway (`chatgpt-revert` - Port 3000)
- **Kiến trúc:** FastAPI + Chrome Extension v1.1.0 (hook trực tiếp `/backend-anon/conversation` và `/backend-api/conversation`).
- **Phản hồi:** Chuẩn SSE JSON Patch `{"v": [{"p": "/parts/0", "o": "append", "v": "..."}]}` -> Chuyển đổi thành OpenAI Streaming format.

### 3.2. Google Gemini Gateway (`gemini-revert` - Port 3001)
- **Kiến trúc:** FastAPI + Chrome Extension v1.2.0 (hook Google `StreamGenerate` kết hợp DOM Stream Observer v1.2.0).
- **Phát hiện Model:** Nhận diện model cấp cao của tài khoản (`Argon High` / Gemini 2.0–2.5 Pro).
- **Hỗ trợ Đa Phương Tiện:** Tự động bắt ảnh Imagen và video Veo, trích xuất Base64 Data URL, chuyển thẳng về client.

### 3.3. GUI Tester Đa Nền Tảng (`H:\reqble-mcp\gui_tester.py`)
- **Công nghệ:** PySide6 + `QWebEngineView` (Chromium nhúng).
- **Tính năng:**
  - Chuyển đổi cổng tức thì (Port 3000: ChatGPT, Port 3001: Gemini, Port 3002: DeepSeek).
  - Trình phát media HTML5 cho hình ảnh độ phân giải cao và video Veo AI.
  - Tự động lưu tất cả media sinh ra vào ổ đĩa cứng `H:\reqble-mcp\media\`.
  - Phím tắt mở thư mục media và xóa chat tức thì.

---

## 4. BẢN THIẾT KẾ DỰ ÁN MỚI: DEEPSEEK GATEWAY (`deepseek-revert` - Port 3002)

### 4.1. Phân Tích Kiến Trúc Web Của DeepSeek (`chat.deepseek.com`)

DeepSeek là nền tảng AI mã nguồn mở hàng đầu thế giới với hai model chủ lực:
1. **DeepSeek-V3:** Model chat siêu tốc độ.
2. **DeepSeek-R1 (Reasoner):** Model suy luận sâu với chuỗi tư duy (Thinking Process).

#### Đặc điểm kỹ thuật Web của DeepSeek:
- **Giao diện:** Xây dựng trên React / Next.js.
- **Khung nhập văn bản:** Thường là thẻ `<textarea id="chat-input">` hoặc `<div contenteditable="true">`.
- **Cơ chế xác thực (Authentication):**
  - Sử dụng JWT Token lưu tại `localStorage.getItem('userToken')` hoặc cookie `ds_session`.
  - Endpoint cấu hình tài khoản: `GET https://chat.deepseek.com/api/v0/users/current`
- **Endpoint sinh phản hồi (Chat Completion):**
  - `POST https://chat.deepseek.com/api/v0/chat/completion`
- **Request Headers đặc trưng:**
  ```http
  Authorization: Bearer <userToken>
  Content-Type: application/json
  X-App-Version: 20241120.0
  ```
- **Request Payload:**
  ```json
  {
    "chat_session_id": "0192e4a8-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "parent_message_id": null,
    "prompt": "Chào DeepSeek, hãy giải bài toán này...",
    "ref_file_ids": [],
    "thinking_enabled": true,
    "search_enabled": false
  }
  ```
  *(Lưu ý: `thinking_enabled: true` kích hoạt DeepSeek-R1 Reasoner, `false` kích hoạt DeepSeek-V3).*

#### Cấu trúc Stream SSE của DeepSeek:
Phản hồi từ `chat.deepseek.com/api/v0/chat/completion` trả về chuẩn `text/event-stream`:
```sse
data: {"v": {"response": {"type": "thinking", "content": "Để giải quyết vấn đề này, trước tiên ta cần xét..."}}}

data: {"v": {"response": {"type": "text", "content": "Kết quả cuối cùng là 42."}}}

data: [DONE]
```
- Khi `type === "thinking"`: Đây là quá trình suy nghĩ của DeepSeek-R1. Chúng ta có thể format thành tag `<think>...</think>` chuẩn như API chính thức của DeepSeek R1!
- Khi `type === "text"`: Nội dung câu trả lời hoàn thiện gửi cho người dùng.

---

### 4.2. Kế Hoạch Triển Khai `deepseek-revert` (Port 3002)

#### Thư mục dự án mục tiêu: `H:\reqble-mcp\deepseek-revert\`
```
H:\reqble-mcp\deepseek-revert\
├── main.py                  # FastAPI Gateway chuẩn OpenAI (Port 3002)
├── api/
│   ├── routes.py            # /v1/chat/completions & /v1/models
│   └── bridge.py            # /bridge/poll_now, /bridge/chunk, /bridge/done
├── extension/               # Chrome Extension cho chat.deepseek.com
│   ├── manifest.json
│   ├── background.js
│   ├── hook.js              # Intercept fetch trên /api/v0/chat/completion
│   └── content.js           # Điều khiển input DeepSeek & chuyển mạch R1/V3
└── start_server.bat         # Khởi động dịch vụ DeepSeek Gateway
```

#### Quy trình điều khiển DOM trên DeepSeek:
1. **Tìm ô nhập liệu:**
   ```javascript
   const textarea = document.querySelector('textarea#chat-input') 
     || document.querySelector('textarea[placeholder*="DeepSeek"]')
     || document.querySelector('div[contenteditable="true"]');
   ```
2. **Kích hoạt chế độ DeepThink (R1) hoặc Web Search:**
   - DeepSeek có 2 nút toggle ngay dưới khung chat:
     - Nút **DeepThink (R1)**: Có class hoặc icon bóng đèn / não.
     - Nút **Tìm kiếm web (Search)**: Icon địa cầu.
   - Extension có thể tự động bấm toggle này dựa trên tham số `model` truyền từ OpenAI API:
     - Model `deepseek-reasoner` hoặc `deepseek-r1` -> Bật DeepThink.
     - Model `deepseek-chat` hoặc `deepseek-v3` -> Tắt DeepThink.
3. **Nhấn nút Gửi:**
   - DeepSeek dùng nút gửi dạng tròn có icon mũi tên:
   ```javascript
   const sendBtn = document.querySelector('div[role="button"][aria-label*="Send"]')
     || document.querySelector('button[aria-label*="Gửi"]')
     || document.querySelector('div.send-button');
   sendBtn.click();
   ```

---

## 5. Bảng So Sánh Các Cổng Reverse Proxy

| Tham số | ChatGPT Gateway | Gemini Gateway | DeepSeek Gateway (Sắp tới) |
| :--- | :--- | :--- | :--- |
| **Port mặc định** | `3000` | `3001` | `3002` |
| **Domain mục tiêu** | `chatgpt.com` | `gemini.google.com` | `chat.deepseek.com` |
| **Model hỗ trợ** | GPT-4o, o1, GPT-4o-mini | Argon High, Gemini 2.0 Pro | DeepSeek-V3, DeepSeek-R1 (Reasoner) |
| **Khả năng Media** | DALL-E 3 | Imagen 3 + Veo Video | LaTeX Math, Code blocks chuyên sâu |
| **Cơ chế bắt stream** | Fetch hook JSON patch | Fetch hook + DOM fallback | Fetch hook SSE `/api/v0/chat/completion` |
| **Tích hợp GUI Tester** | Preset cổng 3000 | Preset cổng 3001 | Preset cổng 3002 |

---

## 6. Checklist Bắt Đầu Dự Án DeepSeek
- [ ] Mở tab `https://chat.deepseek.com` trên Chrome profile thật và đăng nhập.
- [ ] Bật F12 Network tab, gửi câu hỏi để kiểm chứng chính xác schema JSON mới nhất của endpoint `/api/v0/chat/completion`.
- [ ] Khởi tạo khung thư mục `H:\reqble-mcp\deepseek-revert\`.
- [ ] Viết `hook.js` & `content.js` cho DeepSeek.
- [ ] Thêm preset DeepSeek (Port 3002) vào `H:\reqble-mcp\gui_tester.py`.
- [ ] Thử nghiệm suy luận với DeepSeek-R1 Thinking process.


---

## 7. Đỉnh Cao Hợp Nhất: Unified Multi-AI Gateway (Port 3000 & All-in-One Extension)

Để tối ưu hóa trải nghiệm và giảm thiểu tài nguyên hệ thống, kiến trúc tách rời nhiều port (3000, 3001, 3002) đã được nâng cấp thành **Unified AI Gateway** tại `H:\reqble-mcp\unified-ai-gateway`:

### 7.1. Đặc Điểm Kiến Trúc:
- **1 Server Duy Nhất (Port 3000):** Cung cấp API tương thích 100% chuẩn OpenAI tại `http://localhost:3000/v1/chat/completions`.
- **1 Tiện Ích Chrome Duy Nhất (`unified-ai-gateway/extension`):** Tự động nhận diện và nạp worker script phù hợp cho từng tab đang mở:
  - Tab `chatgpt.com` -> Nạp `chatgpt_hook.js` & `chatgpt_content.js`
  - Tab `gemini.google.com` -> Nạp `gemini_hook.js` & `gemini_content.js`
  - Tab `chat.deepseek.com` -> Nạp `deepseek_hook.js` & `deepseek_content.js`
- **Dynamic Model Router:** Khi client gửi request:
  - Nếu `model` chứa `deepseek` hoặc `r1` -> Điều phối job về hàng đợi DeepSeek.
  - Nếu `model` chứa `gemini` -> Điều phối job về hàng đợi Gemini (hỗ trợ cả ảnh và video).
  - Nếu `model` chứa `gpt` hoặc `chatgpt` -> Điều phối job về hàng đợi ChatGPT.
