# Unified AI Web Proxy Gateway

> **All-in-One Local OpenAI-Compatible API Gateway** kết nối trực tiếp với các phiên đăng nhập web thật của **ChatGPT (`chatgpt.com`)**, **Google Gemini (`gemini.google.com`)**, và **DeepSeek (`chat.deepseek.com`)** thông qua 1 Extension trình duyệt duy nhất và 1 cổng Server duy nhất (`port 3000`).

---

## 🌟 Tính Năng Nổi Bật

- **Chuẩn OpenAI API (`/v1/chat/completions` & `/v1/models`):** Tương thích 100% với thư viện `openai` (Python/Node.js), LangChain, LlamaIndex, Open WebUI, Next.js, Cursor,...
- **1 Extension Duy Nhất (`v1.5.0`):** Hoạt động đồng thời trên cả 3 tab AI, không cần cài nhiều extension riêng lẻ.
- **Tự Động Định Tuyến Model (Dynamic Routing):**
  - Model chứa `deepseek`, `r1`, `v3` ➔ Tự động đẩy qua tab **DeepSeek**.
  - Model chứa `gpt`, `chatgpt`, `o1` ➔ Tự động đẩy qua tab **ChatGPT**.
  - Model chứa `gemini` ➔ Tự động đẩy qua tab **Google Gemini**.
- **DeepSeek R1 Thinking:** Tự động bắt chế độ suy nghĩ của DeepSeek và bọc vào thẻ `<think>...</think>`.
- **Gemini Rich Media Capture:** Bắt trọn hình ảnh AI sinh ra (Imagen) và video (Veo), tự động encode sang Base64 Data URL chuẩn Markdown (`![alt](data:image/...)`).
- **ChatGPT JSON-Patch Delta Parser:** Giải mã luồng SSE độc quyền của OpenAI, trả về văn bản Markdown sạch không lẫn metadata rác.
- **Bypass Captcha & Cloudflare Tự Động:** Hoạt động dựa trên session của trình duyệt thật, miễn nhiễm với bot detection.

---

## 📂 Cấu Trúc Dự Án

```
H:\reqble-mcp\unified-ai-gateway\
├── api\
│   ├── app.py                     # Khởi tạo FastAPI & gắn routes
│   ├── middleware.py              # Middleware xác thực Bearer token & CORS
│   ├── routes_bridge.py           # HTTP Bridge giao tiếp 2 chiều với Chrome Extension
│   ├── routes_chat.py             # Endpoint chuẩn /v1/chat/completions (Stream SSE & Non-stream)
│   └── routes_models.py           # Endpoint chuẩn /v1/models
├── core\
│   ├── chatgpt_stream_parser.py   # Bóc tách JSON-Patch RFC 6902 & delta của ChatGPT
│   ├── deepseek_stream_parser.py  # Bóc tách suy nghĩ <think> & delta của DeepSeek
│   ├── gemini_stream_parser.py    # Bóc tách mảng chunk wrb.fr của Gemini
│   └── sse_parser.py              # Định dạng chunk OpenAI chat.completion.chunk
├── providers\
│   ├── base.py                    # Interface BaseProvider chuẩn
│   └── unified_providers.py       # ChatGPTWebProvider, GeminiWebProvider, DeepSeekWebProvider & UnifiedRouter
├── extension\                     # Extension All-in-One cho Chrome
│   ├── manifest.json              # Khai báo manifest v3 (matches cả 3 domain)
│   ├── background.js              # Service worker điều phối và relay API sang localhost:3000
│   ├── chatgpt_hook.js & content.js
│   ├── gemini_hook.js & content.js
│   └── deepseek_hook.js & content.js
├── config.py                      # Cấu hình PORT (3000), API_KEY, DEFAULT_MODEL
├── main.py                        # Điểm khởi chạy server Uvicorn
└── requirements.txt               # Thư viện phụ thuộc
```

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### Bước 1: Khởi Động Server Local

```bash
cd H:\reqble-mcp\unified-ai-gateway
pip install -r requirements.txt
server.bat
```
*Hoặc click đúp chuột vào file `server.bat` ở thư mục gốc `H:\reqble-mcp\server.bat` để bật/tắt nhanh.*

### Bước 2: Cài Đặt Extension vào Trình Duyệt

1. Mở Chrome / Brave / Edge, truy cập: `chrome://extensions/`
2. Bật công tắc **Developer mode (Chế độ dành cho nhà phát triển)** ở góc trên bên phải.
3. Bấm **Load unpacked (Tải tiện ích đã giải nén)**.
4. Chọn thư mục: `H:\reqble-mcp\unified-ai-gateway\extension`.
5. Đảm bảo tiện ích **Unified AI Web Proxy Bridge** đã được bật (Version `1.5.0`).

### Bước 3: Mở Các Tab AI

Đăng nhập tài khoản của bạn và giữ các tab sau mở trên trình duyệt (có thể thu nhỏ cửa sổ xuống taskbar):
- `https://chatgpt.com/`
- `https://gemini.google.com/`
- `https://chat.deepseek.com/`

---

## 🛠️ Hướng Dẫn Gọi API

### 1. Python (Sử dụng thư viện `openai` chính thức)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:3000/v1",
    api_key="sk-unified-local-gateway-key"
)

# Ví dụ 1: DeepSeek R1 (Streaming kèm thẻ <think>)
stream = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role": "user", "content": "1 + 1 bằng mấy?"}],
    stream=True
)
for chunk in stream:
    text = chunk.choices[0].delta.content or ""
    print(text, end="", flush=True)

# Ví dụ 2: ChatGPT GPT-4o (Non-stream)
res = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Viết một bài thơ ngắn về biển"}],
    stream=False
)
print(res.choices[0].message.content)

# Ví dụ 3: Gemini Web (Tạo ảnh)
res = client.chat.completions.create(
    model="gemini-web",
    messages=[{"role": "user", "content": "tạo hình một trái chuối biết bay"}],
    stream=False
)
print(res.choices[0].message.content)
```

### 2. Node.js / TypeScript

```typescript
import OpenAI from "openai";

const openai = new OpenAI({
  baseURL: "http://localhost:3000/v1",
  apiKey: "sk-unified-local-gateway-key",
});

async function main() {
  const stream = await openai.chat.completions.create({
    model: "deepseek-reasoner",
    messages: [{ role: "user", content: "Xin chào!" }],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
}

main();
```

### 3. cURL

```bash
# Lấy danh sách models
curl http://localhost:3000/v1/models \
  -H "Authorization: Bearer sk-unified-local-gateway-key"

# Gửi yêu cầu Chat
curl -N http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-unified-local-gateway-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Chào bạn!"}],
    "stream": true
  }'
```

---

## 📋 Bảng Danh Sách Model Hỗ Trợ

| Model ID | Provider Đích | Đặc tính nổi bật |
|---|---|---|
| `deepseek-reasoner` | DeepSeek | Bật DeepThink (R1), trả về reasoning chain `<think>...</think>` |
| `deepseek-chat` / `deepseek-v3` | DeepSeek | Tắt DeepThink, tốc độ phản hồi cực nhanh |
| `gpt-4o` / `chatgpt-web` | ChatGPT | GPT-4o bản web chuẩn, phân tích đa năng |
| `o1` / `o1-mini` | ChatGPT | Mô hình reasoning của OpenAI |
| `gemini-web` / `gemini-2.5-flash` | Gemini | Sinh văn bản, tạo ảnh Imagen (Base64) & video Veo |

---

## ⚙️ Cấu Hình Nâng Cao (`.env`)

Tạo file `.env` tại thư mục gốc để thay đổi cổng hoặc khóa bảo mật:

```ini
PORT=3000
API_KEY=sk-unified-local-gateway-key
DEFAULT_MODEL=deepseek-reasoner
```
