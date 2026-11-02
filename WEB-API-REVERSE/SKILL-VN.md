---
name: api-reverse-engineer
description: >-
  Framework dịch ngược (reverse engineering) Web API chuẩn production. Sử dụng khi cần trích xuất API,
  reverse backend web service, bắt gói tin mã hóa qua Reqable MITM Proxy,
  vượt hệ thống chống bot (anti-bot fingerprinting) bằng profile GPM Login ẩn danh,
  bắt xác thực JWT/session cookies/CSRF, phát lại hoặc sửa đổi request,
  hoặc tự động tạo SDK client (Python/TypeScript) và đặc tả OpenAPI 3.0.
---

# Kỹ Năng Dịch Ngược Web API (Web API Reverse Engineering)

Một bộ công cụ tự động hóa và phương pháp luận toàn diện, chuẩn production để dịch ngược các giao thức HTTP/1.1, HTTP/2, WebSocket và RESTful API từ bất kỳ ứng dụng web hiện đại nào.

Kỹ năng này tích hợp:
- **Reqable MITM Proxy (`reqable-mcp` trên `127.0.0.1:9000`)**: Engine phân tích gói tin gốc viết bằng C++, bắt traffic trực tiếp, lọc gói tin, quy tắc ghi đè request (Rewrite), điểm ngắt (Breakpoint) và addon script Python động (`reqable.py`).
- **Trình duyệt ẩn danh GPM Login (`gpmlogin` Local API trên `localhost:9495`)**: Các profile trình duyệt chống phát hiện (anti-detect) giả lập Canvas, WebGL, Audio, ClientRects, Fonts và WebRTC, được cấu hình sẵn để điều hướng toàn bộ traffic qua Reqable.
- **Chrome DevTools MCP (`chrome-devtools`)**: Điều khiển trình duyệt trực tiếp, thao tác DOM headless, mô phỏng sự kiện và debug qua giao thức CDP.
- **Engine Bắt Xác Thực (Authentication Capture Engine)**: Trích xuất tạm thời trên bộ nhớ các claim JWT, session cookie và CSRF token kèm cơ chế tự động làm mới token cho client.
- **Các Script Tự Động Hóa Sẵn Dùng (`scripts/`)**: Công cụ dòng lệnh (CLI) để khởi chạy profile, ghi lại traffic, trích xuất auth, chuyển đổi cURL sang client code và tạo đặc tả OpenAPI.

---

## 1. Kiến Trúc Hệ Thống & Luồng Dữ Liệu (Traffic Flow)

Engine dịch ngược kết nối giữa trình duyệt tự động hóa chống phát hiện và bộ phân tích gói tin cấp độ proxy:

```
+─────────────────────────────────────────────────────────────────────────────+
| Profile Trình Duyệt Ẩn Danh GPM Login (Chromium)                            |
| - Chống Fingerprint: Bơm nhiễu Canvas, WebGL, Audio, ClientRects, Fonts    |
| - Bộ nhớ Cookie/Session độc lập                                             |
| - Proxy cấu hình: http://127.0.0.1:9000                                     |
| - Điều khiển qua CDP (remote_debugging_port / websocket_debugging_url)      |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                         Toàn bộ traffic HTTPS / WebSocket
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Reqable MITM Proxy & Engine (127.0.0.1:9000)                                |
| - Giải mã SSL (Reqable Root CA)                                             |
| - Soi gói tin & lọc trực tiếp (capture_live_filter)                         |
| - Can thiệp chủ động (capture_rewrite_*, capture_breakpoint_*)              |
| - Addon Script Python (onRequest / onResponse qua reqable.py)               |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                         Traffic đã giải mã & chuyển tiếp
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Target Web APIs (Cloudflare / Akamai / Custom Endpoints)                     |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                       Các phiên giao dịch bắt được / cURL Logs
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Bộ Công Cụ Tổng Hợp (scripts/)                                              |
| - auth_extractor.py: Trích xuất JWT/cookie vào RAM & tạo file .env          |
| - curl_to_client.py: Tạo SDK typed Python (requests/httpx) & TypeScript      |
| - har_to_openapi.py: Xuất đặc tả OpenAPI 3.0 chuẩn                         |
| - api_analyzer.py: Phân loại endpoint & tạo tài liệu Markdown               |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Ma Trận Phối Hợp Công Cụ

| Công cụ / Hệ thống con | Khả năng chính | Lệnh / API Call trọng tâm |
| :--- | :--- | :--- |
| **`reqable-mcp`** | Điều khiển proxy & bắt traffic trực tiếp | `capture_live_set_enabled`, `capture_live_filter`, `capture_live_get_by_id`, `capture_live_generate_curl`, `capture_live_compose` |
| **`reqable-mcp`** | Quy tắc ghi đè & can thiệp gói tin | `capture_rewrite_create`, `capture_breakpoint_create`, `capture_script_create` |
| **`gpmlogin` Local API** | Quản lý profile chống phát hiện | `GET /profiles`, `POST /profiles/create` (`raw_proxy: 127.0.0.1:9000`), `GET /profiles/start/{id}`, `GET /profiles/stop/{id}` |
| **`chrome-devtools`** | Điều khiển headless & tương tác DOM | `navigate_page`, `click`, `fill`, `evaluate_script`, `list_network_requests` |
| **`scripts/gpm_reqable_launcher.py`** | Khởi chạy trình duyệt ẩn danh | Tiện ích CLI tạo profile GPM kèm bơm nhiễu fingerprint, trỏ qua Reqable proxy |
| **`scripts/traffic_capture.py`** | Ghi lại traffic trực tiếp | Tiện ích CLI thu thập luồng dữ liệu Reqable và xuất ra JSON chuẩn |
| **`scripts/auth_extractor.py`** | Phân tích thông tin xác thực | Trích xuất JWT claims, session cookies, CSRF tokens vào `.env` và session wrapper |
| **`scripts/curl_to_client.py`** | Tự động sinh Client SDK | Chuyển đổi cURL / log giao dịch thành mã Python (`requests`/`httpx`) và TypeScript |
| **`scripts/api_analyzer.py`** | Lập danh mục Endpoint | Tạo tài liệu API Markdown có cấu trúc từ traffic JSON |
| **`scripts/har_to_openapi.py`** | Tạo đặc tả OpenAPI 3.0 | Xuất file OpenAPI 3.0 định dạng YAML/JSON kèm suy luận schema |

---

## 3. Quy Trình Dịch Ngược Chuẩn 6 Giai Đoạn (End-to-End Workflow)

```
Giai đoạn 1: Do thám (Recon) & Nhận diện hệ thống chống Bot
   │
   ▼
Giai đoạn 2: Thiết lập môi trường & Kết nối Proxy
   │
   ▼
Giai đoạn 3: Bắt & Lọc Traffic trực tiếp
   │
   ▼
Giai đoạn 4: Xác thực & Khởi tạo phiên Guest (Guest Session Bootstrapping)
   │
   ▼
Giai đoạn 5: Phát lại Request, Can thiệp & Giả lập Chữ ký
   │
   ▼
Giai đoạn 6: Trích xuất Schema & Tự động tạo mã nguồn Client SDK
```

### Giai đoạn 1: Do thám (Recon) & Nhận diện hệ thống chống Bot

1. **Đánh giá bề mặt mục tiêu**:
   - Kiểm tra trang đích (landing page), các lệnh gọi AJAX và các bundle script public.
   - Nhận diện WAF (Web Application Firewall) và cơ chế chống bot:
     * **Cloudflare Turnstile / Challenge**: Tìm các header `cf-ray`, cookie `cf_clearance`, hoặc iframe Turnstile.
     * **Akamai Bot Manager**: Tìm cookie `_abck`, `bm_sz` hoặc script thu thập sensor data.
     * **Datadome**: Tìm cookie `datadome`, phản hồi lỗi 403 dạng JSON, hoặc pop-up CAPTCHA.
     * **FingerprintJS / CreepJS**: Tìm mã tính toán hash Canvas, WebGL, hoặc Audio trong các file JavaScript của bên thứ ba.
2. **Lựa chọn kiến trúc trình duyệt**:
   - Trang cơ bản không có anti-bot/fingerprint: Dùng trực tiếp Chrome DevTools MCP.
   - Trang được bảo vệ (Cloudflare, Akamai, Datadome): **Bắt buộc dùng Profile GPM Login Ẩn Danh** điều hướng qua proxy Reqable (`127.0.0.1:9000`).

---

### Giai đoạn 2: Thiết lập môi trường & Kết nối Proxy

#### Bước 1: Đảm bảo Reqable Proxy đang lắng nghe
Reqable mặc định lắng nghe trên cổng 9000 (`127.0.0.1:9000` hoặc IP mạng LAN nội bộ `192.168.1.192:9000`).
Kiểm tra kết nối proxy:
```bash
curl -I http://127.0.0.1:9000/
```
Đảm bảo chứng chỉ CA Gốc (Root CA) của Reqable đã được cài đặt và tin cậy trong Kho Chứng Chỉ Hệ Thống (Trusted Root Certification Authorities).

#### Bước 2: Khởi chạy Profile GPM Ẩn Danh kết nối Proxy Reqable
Chạy script `gpm_reqable_launcher.py` để tạo và khởi động profile chống phát hiện:
```bash
python "<skill_dir>/scripts/gpm_reqable_launcher.py" --name "Target_ReverseEng" --proxy "http://127.0.0.1:9000" --start
```
Kết quả trả về dạng JSON:
```json
{
  "success": true,
  "engine": "gpm_login",
  "profile_id": "b34df902-8871-4a1b-9e45-d368e592df81",
  "remote_debugging_port": 54321,
  "websocket_debugging_url": "ws://127.0.0.1:54321/devtools/browser/78a9c...",
  "proxy": "http://127.0.0.1:9000"
}
```

#### Bước 3: Đính kèm tự động hóa trình duyệt (CDP / Chrome DevTools)
Kết nối vào profile đang chạy qua CDP WebSocket URL hoặc cổng `54321` để điều khiển điều hướng và tương tác người dùng.

---

### Giai đoạn 3: Bắt & Lọc Traffic trực tiếp

#### Bước 1: Bật tính năng Live Capture trên Reqable
Gọi qua `reqable-mcp`:
```json
{
  "tool": "capture_live_set_enabled",
  "arguments": { "enabled": true }
}
```

#### Bước 2: Mô phỏng hành động người dùng
Thực hiện các thao tác trên trang web để kích hoạt các endpoint AJAX, GraphQL hoặc REST:
- Chuyển trang, click phân trang, nhập tìm kiếm, cuộn vô tận (infinite scroll).
- Gửi form và mở modal.

#### Bước 3: Lọc & Ghi lại Traffic
Chạy `traffic_capture.py` để ghi lại các giao dịch và loại bỏ các file tĩnh rác:
```bash
python "<skill_dir>/scripts/traffic_capture.py" --host "127.0.0.1" --port 9000 --domain "api.target.com" --duration 20 --output "captured_traffic.json"
```

Hoặc truy vấn nhanh qua `reqable-mcp`:
```json
{
  "tool": "capture_live_filter",
  "arguments": {
    "domain": "api.target.com",
    "limit": 50
  }
}
```

---

### Giai đoạn 4: Xác thực & Khởi tạo phiên Guest

Các Web API hiện đại thường dựa vào phiên khách (guest) ẩn danh hoặc phiên người dùng đã đăng nhập.

#### 1. Khởi tạo phiên Guest (API công khai không cần đăng nhập)
Nhiều nền tảng (như Xueqiu, Bilibili, Reddit, Twitter) cho phép đọc đầy đủ dữ liệu nếu thực hiện bắt tay khởi tạo để lấy cookie guest:
1. Gửi request `GET` đến trang chủ hoặc endpoint khởi tạo (`/`, `/api/init`, `/v1/guest/token`).
2. Trích xuất cookie từ header `Set-Cookie` (ví dụ: `xq_a_token`, `guest_id`, `anon_id`).
3. Lưu cookie vào session jar của HTTP client. Các lệnh gọi API sau đó sẽ hoạt động bình thường mà không cần tài khoản đăng nhập.

#### 2. Trích xuất phiên đăng nhập & Token
Chạy `auth_extractor.py` trên file traffic vừa bắt được:
```bash
python "<skill_dir>/scripts/auth_extractor.py" --input "captured_traffic.json" --output "auth_config.json" --env-file ".env" --wrapper "auth_session.py"
```

Dữ liệu trích xuất bao gồm:
- **JWT Claims**: Giải mã các trường payload (`sub`, `iss`, `roles`, `exp`), tính toán thời gian sống (TTL) và phát hiện token hết hạn.
- **Session Cookies**: Định dạng các chỉ thị `Set-Cookie` thành dictionary sạch.
- **CSRF Tokens**: Tự động phát hiện headers (`x-csrf-token`, `x-xsrf-token`) và cookies (`XSRF-TOKEN`).
- **File `.env` Chuẩn Hóa**: Xuất ra các biến môi trường sẵn sàng nạp vào mã nguồn (`API_ACCESS_TOKEN`, `API_REFRESH_TOKEN`, `API_COOKIE_JAR`).

---

### Giai đoạn 5: Phát lại Request, Can thiệp & Giả lập Chữ ký

Kiểm tra hành vi endpoint và thử nghiệm thay đổi tham số bằng các tính năng can thiệp gói tin của Reqable.

#### 1. Phát lại & Chỉnh sửa Request
Thử lại request đã bắt được với các tham số mới qua `reqable-mcp`:
```json
{
  "tool": "capture_live_compose",
  "arguments": {
    "id": "1042"
  }
}
```

Hoặc xuất ra lệnh cURL độc lập:
```json
{
  "tool": "capture_live_generate_curl",
  "arguments": {
    "id": "1042"
  }
}
```

#### 2. Giả lập Phản hồi (Mocking) & Ghi đè Response
Mô phỏng lỗi server (500), giới hạn tần suất (429) hoặc mock dữ liệu phản hồi mà không cần can thiệp backend:
```json
{
  "tool": "capture_rewrite_create",
  "arguments": {
    "name": "Mock_UserData",
    "mode": 2,
    "url_pattern": "https://api.target.com/v1/user/profile",
    "response_status": 200,
    "response_body": "{\"id\": 999, \"role\": \"admin\", \"balance\": 1000000}"
  }
}
```

#### 3. Điểm Ngắt Thời Gian Thực (Breakpoints)
Tạm dừng request gửi đi hoặc response trả về để kiểm tra hoặc sửa đổi header trước khi chuyển tiếp:
```json
{
  "tool": "capture_breakpoint_create",
  "arguments": {
    "name": "Freeze_Payment_Request",
    "url_pattern": "https://api.target.com/v1/checkout",
    "action": "request"
  }
}
```

#### 4. Tính toán Chữ Ký Động (Scripting Python trên Reqable)
Khi API yêu cầu chữ ký số (MD5 query sign, HMAC-SHA256, mã hóa payload AES), gán script Python vào Reqable qua `capture_script_create`.

Reqable thực thi script Python qua IPC cách ly (`onRequest` và `onResponse`):

```python
# reqable_script_sign.py
from reqable import *
import hashlib
import time

def onRequest(context: Context, request: HttpRequest) -> HttpRequest:
    # 1. Thêm timestamp hiện tại
    ts = str(int(time.time() * 1000))
    request.queries["_t"] = ts
    
    # 2. Sắp xếp query params và tính toán chữ ký MD5
    params = sorted(request.queries.toDict().items())
    raw_str = "&".join(f"{k}={v}" for k, v in params if k != "sign")
    secret_salt = "TargetAppSecretKey2026"
    sign = hashlib.md5(f"{raw_str}&salt={secret_salt}".encode("utf-8")).hexdigest()
    
    request.queries["sign"] = sign
    context.comment = f"Signed at {ts}"
    return request

def onResponse(context: Context, response: HttpResponse) -> HttpResponse:
    return response
```

Đăng ký script với `reqable-mcp`:
```json
{
  "tool": "capture_script_create",
  "arguments": {
    "name": "Auto_MD5_Signer",
    "url_pattern": "https://api.target.com/v1/*",
    "script_path": "C:\\path\\to\\reqable_script_sign.py"
  }
}
```

---

### Giai đoạn 6: Trích xuất Schema & Tự động tạo mã nguồn Client SDK

#### 1. Tạo tài liệu API Markdown có cấu trúc
```bash
python "<skill_dir>/scripts/api_analyzer.py" --input "captured_traffic.json" --output "api_documentation.md"
```
Xuất ra danh mục chi tiết tất cả endpoint, chuẩn hóa URL path (ví dụ `/api/v1/users/:id`), schema của query parameter và body request/response.

#### 2. Tạo đặc tả OpenAPI 3.0
```bash
python "<skill_dir>/scripts/har_to_openapi.py" --input "captured_traffic.json" --output "openapi.yaml" --format yaml
```
Xuất file đặc tả OpenAPI 3.0 sẵn sàng import vào Swagger, Postman hoặc các công cụ sinh code.

#### 3. Tự động sinh SDK Client chuẩn Production
Chuyển đổi lệnh cURL hoặc file traffic JSON thành client Python hoặc TypeScript hoàn chỉnh:

**Sinh Client Python (đồng bộ qua `requests`):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang python-requests --output "target_client.py"
```

**Sinh Client Python (bất đồng bộ qua `httpx`):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang python-httpx --output "async_target_client.py"
```

**Sinh Client TypeScript (qua `fetch`):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang typescript --output "TargetClient.ts"
```

**Các đặc điểm của Client SDK được sinh ra**:
- **Làm sạch Header (Header Hygiene)**: Loại bỏ các pseudo-header của HTTP/2 (`:authority`, `:path`, `:method`) và các header nén không hỗ trợ (`br`, `zstd`).
- **Tham số hóa Token**: Chuyển các bearer token cứng thành tham số khởi tạo và tự động đọc từ biến môi trường (`API_ACCESS_TOKEN`).
- **Xử lý 401 Tự Động**: Tích hợp sẵn hook làm mới token và tự động retry request khi hết hạn.

---

## 4. Chiến Lược Vượt Hệ Thống Chống Bot & Anti-Detection

Các WAF hiện đại áp dụng nhiều lớp phòng thủ. Sử dụng các kỹ thuật sau khi gặp chặn:

| Lớp phòng thủ | Cơ chế | Chiến lược vượt qua |
| :--- | :--- | :--- |
| **Browser Fingerprinting** | Băm Canvas, WebGL, AudioContext, Fonts, ClientRects | Khởi chạy trình duyệt bằng `gpm_reqable_launcher.py`. GPM Login bơm nhiễu toán học vào các API phần cứng, ngăn chặn nhận diện định danh thiết bị. |
| **Uy tín IP của WAF (IP Reputation)** | Datadome / Cloudflare giới hạn tốc độ IP Datacenter/Residential | Cấu hình proxy xoay IP dân cư (Residential/Mobile proxy) trong GPM (`raw_proxy`) hoặc cấu hình proxy upstream trong Reqable. |
| **Cloudflare Turnstile** | Proof-of-work mật mã trong iframe ẩn | Giữ cửa sổ trình duyệt GPM hiển thị (foreground); cho phép mã JavaScript chạy bình thường; tuyệt đối không dùng cờ headless thuần (`--headless=new` sẽ kích hoạt chặn Turnstile). |
| **HTTP/2 Fingerprinting** | Định danh JA3, JA4, và khung SETTINGS của HTTP/2 | Điều hướng request qua thư viện Python `httpx` có bật HTTP/2, hoặc giả lập chính xác header trình duyệt bằng engine của GPM. |
| **Làm sạch Header** | Server từ chối request chứa `:authority` hoặc header viết hoa | Dùng script `curl_to_client.py` để tự động dọn sạch pseudo-header HTTP/2 và các header vận chuyển nguy hiểm. |

---

## 5. Bảng Chẩn Đoán & Khắc Phục Sự Cố

| Hiện tượng / Mã lỗi | Nguyên nhân gốc rễ | Hướng dẫn khắc phục |
| :--- | :--- | :--- |
| **Lỗi SSL Handshake / Chứng chỉ không hợp lệ** | Trình duyệt hoặc client không tin cậy Root CA của Reqable | Mở Reqable -> Certificate Manager -> Cài Root CA vào "Trusted Root Certification Authorities" (Windows) hoặc import vào profile trình duyệt. |
| **HTTP 401 Unauthorized** | Token hết hạn hoặc thiếu auth header | Chạy `auth_extractor.py` để kiểm tra `_is_expired` và `_ttl_seconds` của JWT. Chạy lại quy trình capture đăng nhập hoặc bootstrap guest để lấy token mới. |
| **HTTP 403 Forbidden / Cloudflare Challenge** | Bị phát hiện bot do dùng headless browser hoặc fingerprint bất thường | Tắt Chrome mặc định. Mở profile ẩn danh bằng `gpm_reqable_launcher.py`. Tránh dịch chuyển chuột tức thì, mô phỏng độ trễ tự nhiên của người dùng. |
| **HTTP 429 Too Many Requests** | Vượt quá giới hạn tần suất trên IP hoặc token người dùng | Kiểm tra các header `X-RateLimit-Reset` và `Retry-After`. Thêm thuật toán lùi theo hàm mũ (exponential backoff) vào mã client. Đổi proxy IP trên GPM nếu bị chặn IP. |
| **Cổng 9495 Connection Refused (GPM API)** | Ứng dụng GPM Login chưa bật hoặc cổng bị chiếm | Khởi động phần mềm GPM Login. Nếu cổng 9495 bận, kiểm tra cổng động được ghi tại file `%LOCALAPPDATA%\GPMLogin\http.port`. |
| **Cổng 9000 Connection Refused (Reqable)** | Ứng dụng Reqable hoặc dịch vụ proxy bị tắt | Mở phần mềm Reqable và đảm bảo trạng thái Proxy đang kích hoạt (chấm xanh lá ở thanh trạng thái dưới cùng). |
| **Traffic trống khi chạy `traffic_capture.py`** | Proxy bị bỏ qua hoặc tính năng live capture chưa bật | Kiểm tra `raw_proxy: http://127.0.0.1:9000` trong profile GPM. Đảm bảo `capture_live_set_enabled` đã đặt thành `true`. |
| **Lỗi Encoding / Body phản hồi bị rác** | Phản hồi bị nén dạng `zstd` hoặc `br` | Xóa `Accept-Encoding: br, zstd` trong request headers, hoặc bật tính năng tự động giải nén trong Reqable / `httpx`. |
