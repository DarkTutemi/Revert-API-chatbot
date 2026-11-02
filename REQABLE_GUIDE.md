# CẨM NANG TOÀN TẬP VỀ REQABLE: KIẾN TRÚC, KỸ THUẬT VẬN HÀNH, SCRIPTING, MCP VÀ REVERSE ENGINEERING CHUYÊN SÂU

> **Phiên bản tài liệu:** 3.3.x+  
> **Ngôn ngữ:** Tiếng Việt (Vietnamese)  
> **Mục tiêu:** Cung cấp tài liệu tra cứu kỹ thuật toàn diện, chi tiết từ mức cơ bản đến nâng cao về Reqable, bao gồm cấu trúc menu, phím tắt, các công cụ can thiệp lưu lượng, lập trình kịch bản Python, tích hợp giao thức Model Context Protocol (MCP) cho AI Agent, giải pháp bypass SSL Pinning trên Android từ phiên bản 7 đến 15, kiến trúc Report Server và các kịch bản dịch ngược thực chiến.

---

## MỤC LỤC

1. [TỔNG QUAN & KIẾN TRÚC HỆ THỐNG REQABLE](#1-tổng-quan--kiến-trúc-hệ-thống-reqable)
   - 1.1. Triết lý thiết kế và mô hình Dual-Mode (API Testing + Traffic Sniffing)
   - 1.2. Kiến trúc Native C++ Core Engine kết hợp Flutter GUI
   - 1.3. Mô hình xử lý dữ liệu và đa luồng
   - 1.4. Bảng so sánh chuyên sâu: Reqable vs Charles Proxy vs Fiddler Everywhere vs Postman
2. [HƯỚNG DẪN CHI TIẾT TỪNG MENU HỆ THỐNG (UI THỰC TẾ)](#2-hướng-dẫn-chi-tiết-từng-menu-hệ-thống-ui-thực-tế)
   - 2.1. Menu `File` — Quản lý phiên và tab làm việc
   - 2.2. Menu `Tools` — Bộ công cụ trợ lực, mật mã học & tích hợp AI
   - 2.3. Menu `View` — Điều khiển bố cục, các bảng điều hướng & chế độ hiển thị
   - 2.4. Menu `Traffic` — Trái tim can thiệp, định tuyến & bắt gói tin
   - 2.5. Menu `Proxy` — Cấu hình cổng mạng, giao thức & định tuyến ra ngoài
   - 2.6. Menu `Certificate` — Quản lý chứng chỉ Root CA & SSL tùy biến
   - 2.7. Menu `Help` — Tài liệu, kiểm tra cập nhật & cộng đồng
   - 2.8. Ma trận tra cứu phím tắt toàn năng (Comprehensive Shortcuts Matrix)
3. [CHUYÊN SÂU TÍNH NĂNG TRAFFIC MANIPULATION](#3-chuyên-sâu-tính-năng-traffic-manipulation)
   - 3.1. Rewrite Rules — 5 chế độ can thiệp tự động
   - 3.2. Breakpoint Rules — Can thiệp và chỉnh sửa dữ liệu thời gian thực
   - 3.3. Mirror Rules — Ánh xạ tên miền và chuyển hướng Host
   - 3.4. Gateway Rules — Kiểm soát lưu lượng L4 (Network) và L7 (Application)
   - 3.5. Reverse Proxy — Cầu nối trong suốt bypass cài đặt chứng chỉ
   - 3.6. Network Throttling — Giả lập điều kiện mạng thực tế và Chaos Testing
4. [PYTHON SCRIPTING TOÀN DIỆN](#4-python-scripting-toàn-diện)
   - 4.1. Kiến trúc IPC Subprocess và vòng đời Request/Response
   - 4.2. Khảo sát chi tiết mô hình dữ liệu (Data Models API)
   - 4.3. Cơ chế chia sẻ trạng thái liên tiến trình (`context.shared`)
   - 4.4. Bộ 5 mẫu kịch bản Python thực chiến hoàn chỉnh
5. [REQABLE MCP SERVER & TÍCH HỢP AI AGENT](#5-reqable-mcp-server--tích-hợp-ai-agent)
   - 5.1. Kiến trúc kết nối Model Context Protocol (MCP) trong Reqable
   - 5.2. Cấu hình MCP Server (`.mcp.json`) và phân quyền công cụ
   - 5.3. Danh mục hơn 100 công cụ MCP theo nhóm chức năng
   - 5.4. Bảng đối chiếu API REST nội bộ của Reqable
   - 5.5. Kịch bản phối hợp AI Agent tự động hóa điều tra và xử lý lỗi
6. [ANDROID TRAFFIC CAPTURE & SSL PINNING BYPASS](#6-android-traffic-capture--ssl-pinning-bypass)
   - 6.1. Tiến trình siết chặt bảo mật SSL từ Android 7 đến Android 15
   - 6.2. Phân tích thư viện `android-certificate-trust` (AAR)
   - 6.3. Cài đặt System Root CA (OpenSSL Hash, ADB 1-Click & Magisk Module)
   - 6.4. Các sắc thái đặc thù của Chrome và Mozilla Firefox trên Android
   - 6.5. Chiến lược bypass SSL Pinning toàn diện (Java, Frida, LSPosed, Recompilation)
7. [REPORT SERVER & TỰ ĐỘNG HÓA DAST](#7-report-server--tự-động-hóa-dast)
   - 7.1. Kiến trúc Report Server và giao thức xuất dữ liệu HAR
   - 7.2. Phân tích mã nguồn triển khai FastAPI (`report-server-example`)
   - 7.3. Thiết lập hệ thống kiểm thử bảo mật tự động (DAST Pipeline)
8. [5 CASE STUDY THỰC CHIẾN REVERSE ENGINEERING](#8-5-case-study-thực-chiến-reverse-engineering)
   - 8.1. Case Study 1: Bắt trọn vẹn Traffic ứng dụng Flutter (Mobile TUN VPN + Root CA)
   - 8.2. Case Study 2: Ép ứng dụng Desktop né proxy đi qua Reqable với Proxifier
   - 8.3. Case Study 3: Dịch ngược API mã hóa đối xứng AES & ký số MD5 động
   - 8.4. Case Study 4: Debug CLI Scripts & Automation Tools bằng Proxy Terminal 1-Click
   - 8.5. Case Study 5: Mock dữ liệu lỗi & Chaos Engineering cho Mobile App

---

# 1. TỔNG QUAN & KIẾN TRÚC HỆ THỐNG REQABLE

## 1.1. Triết lý thiết kế và mô hình Dual-Mode (API Testing + Traffic Sniffing)

Trong quy trình phát triển phần mềm và bảo mật truyền thống, các kỹ sư thường phải duy trì đồng thời hai công cụ riêng biệt:
- **Công cụ kiểm thử API (API Client):** Điển hình là Postman, Insomnia hoặc Hoppscotch — chuyên phục vụ việc soạn thảo, gửi request REST/gRPC/WebSocket, quản lý biến môi trường và thiết kế bộ sưu tập API.
- **Công cụ bắt chặn gói tin (HTTP/HTTPS Sniffer / MITM Proxy):** Điển hình là Charles Proxy, Fiddler Classic, Fiddler Everywhere hoặc mitmproxy — chuyên lắng nghe proxy hệ thống, phân tích lưu lượng mạng, giải mã SSL và can thiệp gói tin.

Sự tách rời này dẫn đến sự gián đoạn luồng làm việc (context switching): Khi một ứng dụng di động bị lỗi kết nối, kỹ sư phải mở Charles để xem gói tin bị lỗi gì, sao chép URL và headers sang Postman để tái tạo và chỉnh sửa, rồi lại quay lại ứng dụng để kiểm tra.

**Reqable phá vỡ rào cản này bằng kiến trúc Dual-Mode đột phá:**
- **Capture Mode (Chế độ Bắt gói tin):** Đóng vai trò là một máy chủ Proxy trung gian (Man-in-the-Middle - MITM) mạnh mẽ, tự động bắt toàn bộ lưu lượng HTTP/1.1, HTTP/2, HTTP/3 (QUIC) và WebSocket từ trình duyệt, ứng dụng di động, giả lập hoặc ứng dụng desktop.
- **API Testing Mode (Chế độ Kiểm thử API):** Cung cấp giao diện trực quan hoàn chỉnh để gửi request độc lập, hỗ trợ HTTP REST, HTTP Raw, WebSocket, gRPC với Protobuf schema, quản lý biến môi trường phân tầng (Environment / Global), Cookie jar tự động và trích xuất cURL hai chiều.
- **Cơ chế tương tác liền mạch:** Bất kỳ gói tin nào xuất hiện trong bảng Capture đều có thể được chuyển đổi ngay lập tức thành một tab API Testing bằng tính năng *Compose* (`Shift + Ctrl + Enter`) hoặc lưu thẳng vào API Collection (`Ctrl + I`) chỉ với 1 cú click chuột.

```
       +-------------------------------------------------------------+
       |                        REQABLE CORE                         |
       |  +---------------------------+ +-------------------------+  |
       |  |       CAPTURE MODE        | |    API TESTING MODE     |  |
       |  |  - MITM Proxy Engine      | |  - REST / Raw / WS      |  |
       |  |  - SSL Decryption         | |  - gRPC / Protobuf      |  |
       |  |  - Rewrite / Breakpoint   | |  - Collections / Envs   |  |
       |  |  - Gateway / Mirror       | |  - Automated Testing    |  |
       |  +---------------------------+ +-------------------------+  |
       |                ▲                            │               |
       |                └────── COMPOSE / IMPORT ────┘               |
       +-------------------------------------------------------------+
```

## 1.2. Kiến trúc Native C++ Core Engine kết hợp Flutter GUI

Một trong những hạn chế lớn nhất của các công cụ proxy hiện đại (như Fiddler Everywhere hoặc Postman) là chúng được xây dựng trên nền tảng **Electron (Chromium + Node.js)** hoặc **Java Virtual Machine (JVM)** (như Charles Proxy hay Burp Suite), dẫn đến:
- Tốc độ khởi động chậm chạp (thường mất từ 5-15 giây).
- Tiêu thụ bộ nhớ RAM khổng lồ (thường xuyên vượt quá 1GB đến 2GB RAM khi bắt hàng trăm nghìn gói tin).
- Độ trễ mạng (latency overhead) cao do cơ chế Garbage Collection (GC) của JVM hoặc JavaScript engine.

**Reqable giải quyết bài toán hiệu năng bằng sự kết hợp kiến trúc phân tầng độc đáo:**
1. **Lớp Lõi Xử Lý Mạng (Network Engine):** Được viết hoàn toàn bằng **C++ nguyên bản (Native C++)**. Engine này chịu trách nhiệm:
   - Quản lý các socket mạng phi đồng bộ (asynchronous non-blocking I/O) sử dụng `epoll` trên Linux/Android, `kqueue` trên macOS/iOS và `IOCP` (I/O Completion Ports) trên Windows.
   - Xử lý mã hóa/giải mã SSL/TLS hiệu năng cao bằng BoringSSL/OpenSSL.
   - Quản lý bộ nhớ đệm (ring buffer) và zero-copy packet processing, cho phép xử lý hàng chục nghìn kết nối đồng thời với độ trễ gần như bằng không.
2. **Lớp Giao Diện Người Dùng (GUI Layer):** Được phát triển bằng **Google Flutter (Dart)**:
   - Giao diện được vẽ trực tiếp bằng Skia/Impeller graphics engine, đạt tốc độ khung hình 60-120 FPS mượt mà.
   - Thống nhất trải nghiệm thị giác và logic điều khiển 100% trên cả 5 nền tảng: Windows, macOS, Linux, Android và iOS.
   - Kích thước bộ cài siêu nhẹ (~30MB) và khởi động tức thì chỉ trong vòng chưa đầy 1 giây.

## 1.3. Mô hình xử lý dữ liệu và đa luồng

Khi Reqable hoạt động, các luồng xử lý được phân tách nghiêm ngặt để đảm bảo an toàn dữ liệu và không làm nghẽn giao diện:
- **Proxy Listening Thread:** Lắng nghe kết nối TCP từ Client trên cổng cấu hình (mặc định 9000).
- **SSL Handshake Worker Pool:** Nhóm luồng chuyên dụng thực hiện bắt tay TLS với Client và Server đích, tự động sinh chứng chỉ động (dynamic certificate generation).
- **Rule Evaluation Pipeline:** Luồng kiểm tra điều kiện tuần tự: `Access Control` $\to$ `Gateway (L4)` $\to$ `Mirror` $\to$ `Gateway (L7)` $\to$ `Rewrite / Breakpoint / Script`.
- **UI Event Dispatcher:** Sử dụng cơ chế batching (gom nhóm sự kiện) để đẩy dữ liệu lên cây danh sách Traffic List, tránh hiện tượng quá tải rendering khi ứng dụng client gửi request với tần suất lớn.
- **IPC Script Subprocess:** Khi tính năng Python Script được kích hoạt, Reqable không chạy Python bên trong tiến trình chính mà fork một subprocess độc lập để cách ly hoàn toàn, đảm bảo nếu script Python bị lỗi (hoặc crash bộ nhớ), Reqable vẫn vận hành ổn định.

```
Client App ---> [Proxy Socket (IOCP/epoll)] ---> [SSL Termination & MITM Engine]
                                                        │
    ┌───────────────────────────────────────────────────┴────────────────────────────────┐
    ▼                                                   ▼                                ▼
[Gateway L4 / Access Control]            [Mirror / Host Redirection]         [Gateway L7 Filter]
    │                                                   │                                │
    └───────────────────────────────────────────────────┬────────────────────────────────┘
                                                        │
                       [Traffic Manipulation Pipeline: Rewrite / Breakpoint / Python]
                                                        │
                      ┌─────────────────────────────────┴────────────────────────────────┐
                      ▼                                                                  ▼
             [Remote Target Server]                                            [UI List & Storage Engine]
```

## 1.4. Bảng so sánh chuyên sâu: Reqable vs Charles Proxy vs Fiddler Everywhere vs Postman

| Tiêu Chí Kỹ Thuật | Reqable (v3.3+) | Charles Proxy (v4.6+) | Fiddler Everywhere (v5+) | Postman (v11+) |
| :--- | :--- | :--- | :--- | :--- |
| **Công Nghệ Cốt Lõi** | **Native C++ + Flutter UI** | Java (JVM) | Electron (Chromium + .NET) | Electron (Chromium + Node) |
| **Mức Tiêu Thụ RAM Khi Chạy**| **Cực thấp (~80MB - 200MB)**| Trung bình (~400MB - 1GB)| Cao (~800MB - 2GB+) | Rất cao (~1GB - 2.5GB) |
| **Tốc Độ Khởi Động** | **Tức thì (< 1 giây)** | Chậm (~5 - 10 giây) | Rất chậm (~10 - 20 giây) | Chậm (~8 - 15 giây) |
| **Hỗ Trợ Nền Tảng** | Windows, macOS, Linux, Android, iOS | Windows, macOS, Linux | Windows, macOS, Linux | Windows, macOS, Linux (Web) |
| **Hỗ Trợ HTTP/2 & HTTP/3** | **Đầy đủ HTTP/1.1, HTTP/2, HTTP/3 (QUIC)**| Chỉ HTTP/1.1, HTTP/2 | Chỉ HTTP/1.1, HTTP/2 | Chỉ HTTP/1.1, HTTP/2 |
| **Giao Thức WebSocket** | **Bắt gói + Kiểm thử Client độc lập** | Chỉ bắt gói tin | Bắt gói + Gửi frame cơ bản | Hỗ trợ kiểm thử WebSocket |
| **Giao Thức gRPC & Protobuf**| **Server Reflection + Local Proto Schema**| Hạn chế (cần plugin) | Cần cấu hình phức tạp | Hỗ trợ gRPC GUI |
| **Môi Trường Scripting** | **Python 3 Native (Full Thư Viện Cục Bộ)** | Không hỗ trợ | JavaScript (Hạn chế) | JavaScript (Node Sandbox) |
| **Tích Hợp AI (MCP Server)**| **Tích hợp sẵn chuẩn Model Context Protocol**| Không hỗ trợ | Không hỗ trợ | Hỗ trợ Postman AI riêng |
| **Bắt Gói Mobile Độc Lập**| **Có App Mobile (Android/iOS) + VPN TUN**| Không có app bắt gói riêng| Không có app mobile | Không có app bắt gói mạng |
| **Mô Hình Bản Quyền** | Community (Miễn phí) / Bản quyền giá rẻ | Trả phí trọn đời (License) | Thuê bao đắt đỏ (Subscription)| Freemium / Thuê bao đội ngũ |

---

# 2. HƯỚNG DẪN CHI TIẾT TỪNG MENU HỆ THỐNG (UI THỰC TẾ)

Giao diện Reqable được thiết kế trực quan theo chuẩn công nghiệp, với thanh Menu hệ thống ở trên cùng gồm 7 nhóm chính. Phần dưới đây phân tích chi tiết từng mục menu, thông số cấu hình và phím tắt tương ứng được trích xuất trực tiếp từ giao diện thực tế.

```
+----------------------------------------------------------------------------------------------------------------------+
|  File    Tools    View    Traffic    Proxy    Certificate    Help                            [ 192.168.1.100:9000 ● ]|
+----------------------------------------------------------------------------------------------------------------------+
|  [►] Record  | [Terminal] [Device] [Throttling] [Gateway] [Rewrite] [Breakpoint] [Script]   |  Search: [...........] |
+----------------------------------------------------------------------------------------------------------------------+
```

## 2.1. Menu `File` — Quản lý phiên và tab làm việc

Menu `File` đảm nhiệm việc khởi tạo các tab kiểm thử API mới, đọc ghi file dữ liệu bắt gói và quản lý vòng đời ứng dụng.

| Mục Menu | Phím Tắt | Phân Loại | Mô Tả Chức Năng Chi Tiết & Hành Vi Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| **New HTTP** | `Ctrl + T` | Action | Tạo một tab kiểm thử HTTP REST API mới. Hỗ trợ giao diện GUI nhập liệu chuyên nghiệp: chọn Method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, CONNECT, TRACE), nhập URL, bảng Query Parameters, Headers, Body (none, form-data, x-www-form-urlencoded, raw JSON/XML/Text, binary), cài đặt Authorization (Bearer, Basic, API Key, OAuth) và cấu hình metrics thời gian phản hồi. |
| **New HTTP (Raw)** | *Không* | Action | Tạo tab kiểm thử HTTP bằng cách nhập trực tiếp toàn bộ văn bản HTTP message thuần túy (Raw format). Bộ phân tích cú pháp C++ của Reqable sẽ tự động bóc tách Request Line, Headers và Message Body theo chuẩn RFC 7230. |
| **New WebSocket** | *Không* | Action | Mở tab kiểm thử WebSocket độc lập. Hỗ trợ kết nối cả `ws://` và `wss://`, gửi nhận các frame dạng Text UTF-8 hoặc Binary Hex, quản lý bắt tay (handshake headers), duy trì Heartbeat (Ping/Pong) và gắn thẻ lưu vào Collection với nhãn WS. |
| **Open File** | `Ctrl + O` | Action | Mở các file phiên làm việc đã lưu từ ổ đĩa máy tính. Hỗ trợ 3 định dạng tiêu chuẩn: `.har` (HTTP Archive tiêu chuẩn quốc tế), `.reqable` (phiên lưu trữ nội bộ đầy đủ siêu dữ liệu của Reqable), và `.chls` (phiên bắt gói xuất từ Charles Proxy). |
| **Open Recent** | *Không* | Submenu | Hiển thị danh sách các tệp dự án, file phiên bắt gói hoặc tệp HAR vừa được mở trong các phiên làm việc gần nhất để người dùng mở lại nhanh chóng. |
| **Open from Clipboard** | `Shift + Ctrl + O` | Action | Đọc dữ liệu từ bộ nhớ tạm của hệ điều hành (Clipboard). Reqable tự động nhận diện định dạng: Nếu là chuỗi lệnh `curl 'https://...'`, nó sẽ tự parse thành tab HTTP; nếu là nội dung HAR JSON hoặc bản tin HTTP raw, nó sẽ mở giao diện kiểm tra tương ứng. |
| **Close Tab** | `Ctrl + W` | Action | Đóng tab làm việc đang được trỏ chuột hiện tại. Tương đương với thao tác nhấp chuột giữa vào tiêu đề tab. |
| **Close All Tabs** | `Shift + Ctrl + W` | Action | Đóng toàn bộ các tab đang mở trên thanh tab bar, dọn dẹp không gian làm việc. |
| **Quit Reqable** | `Ctrl + Q` | Action | Thoát ứng dụng hoàn toàn. **Cơ chế an toàn:** Trước khi thoát tiến trình, Reqable sẽ tự động khôi phục cấu hình Proxy hệ điều hành (Windows Internet Settings) về trạng thái ban đầu, đảm bảo máy tính không bị mất kết nối Internet. |

---

## 2.2. Menu `Tools` — Bộ công cụ trợ lực, mật mã học & tích hợp AI

Menu `Tools` cung cấp hệ thống tiện ích phụ trợ mạnh mẽ nhất dành cho lập trình viên, chuyên gia bảo mật và tích hợp trí tuệ nhân tạo.

```
Tools
 ├── Command Palette          [ Shift + Ctrl + P ]
 ├── Proxy Terminal           [ Alt + T ]
 ├── Script Environment
 ├── MCP                      (Model Context Protocol)
 ├── cURL Options
 ├── gRPC
 ├── Protobuf
 ├── Access Token
 ├── Decode >                 [ URL | Base64 | Hex | Unicode | JWT | Gzip ]
 ├── Encode >                 [ URL | Base64 | Hex | Unicode | JSON Escape ]
 ├── Hash >                   [ MD5 | SHA1 | SHA224 | SHA256 | SHA384 | SHA512 ]
 ├── HMAC >                   [ HMAC-MD5 | HMAC-SHA1 | HMAC-SHA256 | HMAC-SHA512 ]
 ├── Encrypt >                [ AES (ECB, CBC, CFB, OFB, CTR, GCM) ]
 ├── Decrypt >                [ AES Decryption with Auto-unpad ]
 ├── View >                   [ Hex | JSON Tree | XML | Color | Image ]
 ├── Timestamp                (Unix Epoch <-> Date Time)
 ├── UUID                     (UUID v4 Generator)
 ├── Regex                    (Visual Regular Expression Tester)
 └── QR-Code                  (Generator & Screen Scanner)
```

### Chi tiết các phân mục trong Menu `Tools`:

1. **Command Palette (`Shift + Ctrl + P`):** Hộp thoại điều khiển tập trung tương tự VS Code. Cho phép tìm kiếm nhanh và thực thi tức thời bất kỳ hành động nào trong ứng dụng mà không cần duyệt menu chuột (như chuyển port, nạp script, bật chế độ ẩn danh...).
2. **Proxy Terminal (`Alt + T`):** Khởi chạy một cửa sổ dòng lệnh (PowerShell/CMD trên Windows, Terminal trên macOS, Bash trên Linux) đã được **tiêm sẵn (injected) toàn bộ biến môi trường proxy và chứng chỉ SSL CA**. Giúp các công cụ CLI (`curl`, `git`, `pip`, `npm`, `python requests`) tự động kết nối qua Reqable mà không gặp lỗi từ chối chứng chỉ.
3. **Script Environment:** Quản lý môi trường thực thi Python 3 cho tính năng Script. Cho phép chỉ định đường dẫn thực thi `PYTHON_HOME` hoặc file binary của Python (yêu cầu Python $\ge$ 3.6), hỗ trợ các môi trường ảo (venv, conda).
4. **MCP (Model Context Protocol):** Cung cấp hướng dẫn và kích hoạt máy chủ MCP Server tích hợp sẵn. Cho phép kết nối trực tiếp với các AI Agent (như Claude Desktop, Cursor, Antigravity) để AI tự động truy vấn traffic, tạo quy tắc can thiệp và phân tích lỗ hổng.
5. **cURL Options:** Cấu hình chuẩn hóa khi sinh lệnh cURL: chọn định dạng xuống dòng (Single-line / Multi-line), loại dấu ngoặc kép (`"` cho Windows cmd hoặc `'` cho bash), bật cờ `--location` tự động theo chuyển hướng, hoặc thêm cờ `-k` / `--insecure`.
6. **gRPC:** Quản lý định nghĩa dịch vụ gRPC Proto theo tên miền. Hỗ trợ 3 nguồn dữ liệu schema:
   - **Server Reflection:** Tự động truy vấn schema từ máy chủ gRPC đích nếu server bật reflection.
   - **Local File:** Nạp trực tiếp các file `.proto` lưu trữ trên ổ đĩa.
   - **Spec File:** Sử dụng file đặc tả API được lưu và đồng bộ qua đám mây của Reqable.
7. **Protobuf:** Quản lý ánh xạ URL sang các schema Google Protocol Buffers để tự động giải mã các gói tin nhị phân Protobuf thành định dạng JSON dễ đọc.
8. **Access Token:** Trình quản lý Bearer / OAuth Tokens tập trung, cho phép cấu hình và tái sử dụng token xác thực trên nhiều API request khác nhau.
9. **Bộ công cụ chuyển đổi & Mật mã học (Codec & Cryptography):**
   - **Decode / Encode:** Chuyển đổi hai chiều cho URL Encoding, Base64 (hỗ trợ preview ảnh), Hexadecimal, Unicode (`\uXXXX`), JSON Escape, và JWT Decoder (phân tích phần Header, Payload claims, giải mã thời gian hết hạn `exp`).
   - **Hash:** Tính toán Message Digest cho chuỗi hoặc file: MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512 (hỗ trợ cả chuỗi rỗng theo chuẩn RFC).
   - **HMAC:** Tính mã xác thực tin nhắn dựa trên băm: HMAC-MD5, HMAC-SHA1, HMAC-SHA256, HMAC-SHA512 với Key và Payload tùy biến.
   - **Encrypt / Decrypt (AES):** Hỗ trợ toàn diện thuật toán mã hóa đối xứng Advanced Encryption Standard (AES) với đầy đủ các chế độ: ECB, CBC, CFB, OFB, CTR, GCM; các chuẩn đệm (Padding): PKCS#7, None; hỗ trợ Key và IV ở định dạng Plaintext, Hex hoặc Base64.
10. **Trình xem nội dung chuyên biệt (Viewers):**
    - **Hex Viewer:** Phân tích dữ liệu ở dạng bảng thập lục phân (Offset, Hex Dump, ASCII representation).
    - **JSON / XML Viewer:** Định dạng (Beautify/Minify), hiển thị cây phân cấp (Tree View), tìm kiếm node theo JSONPath hoặc XPath.
    - **Color Viewer:** Xem và trích xuất mã màu (HEX, RGB, HSL).
    - **Image Viewer:** Xem ảnh trực tiếp từ payload HTTP, hỗ trợ định dạng PNG, JPG, GIF, WebP, SVG, AVIF, APNG và Data URL Base64.
11. **Tiện ích chuyển đổi số liệu:**
    - **Timestamp:** Chuyển đổi tức thì giữa Unix Timestamp (giây hoặc mili-giây) và định dạng ngày giờ chuẩn (`yyyy-MM-dd HH:mm:ss`).
    - **UUID:** Sinh mã UUID định dạng chuẩn Version 4 (sinh đơn lẻ hoặc sinh hàng loạt).
    - **Regex:** Trình kiểm thử Regular Expression tương tác, hiển thị trực quan các cụm khớp (matches) và các nhóm bóc tách (capturing groups) với các cờ `i` (ignore case), `m` (multiline), `s` (dotall).
    - **QR-Code:** Tạo mã QR từ chuỗi văn bản hoặc quét bóc tách mã QR từ file ảnh chụp màn hình.

---

## 2.3. Menu `View` — Điều khiển bố cục, các bảng điều hướng & chế độ hiển thị

Menu `View` quản lý các ngăn điều hướng bên hông (Sidebar Panels), hướng bố cục vùng làm việc chính và tỉ lệ thu phóng màn hình.

| Mục Menu | Phím Tắt | Phân Loại | Chức Năng Chi Tiết |
| :--- | :--- | :--- | :--- |
| **Explorer** | `F1` | Panel Toggle | Mở/đóng cây phân cấp cấu trúc (Structure Tree) của luồng bắt gói tin. Cây phân cấp tự động gom nhóm theo cấu trúc: `Device -> Application -> Domain -> Path`. Cho phép lọc nhanh toàn bộ traffic theo một tiến trình hoặc một tên miền cụ thể. |
| **Collection** | `F2` | Panel Toggle | Mở/đóng ngăn quản lý danh mục API Collections. Cho phép tổ chức thư mục, nhóm API theo dự án, chia sẻ đồng bộ Cloud, tạo tài liệu API Documentation và chạy kịch bản kiểm thử tự động. |
| **Environment** | `F3` | Panel Toggle | Mở/đóng bảng quản lý biến môi trường. Hỗ trợ cấu hình các biến cho từng môi trường (Dev, Staging, Production) và Global Environment, danh sách các biến động hệ thống (`$date`, `$guid`, `$timestamp`, `$randomInt`...). |
| **History** | `F4` | Panel Toggle | Mở/đóng lịch sử các phiên bắt gói và lịch sử gửi yêu cầu API. Hỗ trợ tìm kiếm theo mốc thời gian, lọc theo URL, xóa theo nhóm và cấu hình thời hạn lưu trữ (Retention Policy). |
| **Device** | `F5` | Panel Toggle | Mở/đóng danh sách các thiết bị di động đang kết nối từ xa với Reqable Desktop qua chế độ Collaborative Mode. Sẽ tự động ẩn đi nếu Reqable đang bật tùy chọn *Listen on Loopback*. |
| **Toolbox** | `F6` | Panel Toggle | Mở/đóng thanh công cụ mini tích hợp ở mép trái giao diện (chứa phím tắt truy cập nhanh Regex, Codec, Crypto, Formatters). |
| **Expand Sidebar** | `Shift + Ctrl + [` | Layout Action | Thu gọn hoặc mở rộng toàn bộ thanh Sidebar bên trái để tối ưu diện tích hiển thị. |
| **Vertical Layout** | `Shift + Ctrl + ]` | Layout Action | Chuyển đổi hướng hiển thị chi tiết của cặp Request/Response: luân chuyển giữa bố cục dọc (Vertical - chia nửa trên là Request, nửa dưới là Response) và bố cục ngang (Horizontal - chia nửa trái là Request, nửa phải là Response). |
| **Zen Mode** | `Shift + Ctrl + \` | Layout Action | Kích hoạt chế độ tập trung cao độ (Zen Mode): Ẩn toàn bộ thanh Sidebar và các thành phần phụ trợ, tab Traffic chỉ hiển thị các icon thu nhỏ, tối đa hóa không gian màn hình cho danh sách gói tin và chi tiết payload. |
| **Custom Toolbar** | *Không* | Dialog Action | Tùy biến thanh công cụ nhanh trên đỉnh giao diện: Cho phép người dùng ghim hoặc bỏ ghim các nút chức năng hay dùng (Proxy Terminal, Network Throttling, Script, Gateway, Reverse Proxy...). |
| **Zoom In** | `Ctrl + =` | UI Action | Phóng to tỉ lệ hiển thị giao diện Reqable (tăng kích thước font chữ, icon, bảng biểu). |
| **Zoom Out** | `Ctrl + -` | UI Action | Thu nhỏ tỉ lệ hiển thị giao diện Reqable. |
| **Zoom Reset** | *Không* | UI Action | Khôi phục tỉ lệ hiển thị giao diện về mặc định gốc (100%). |

---

## 2.4. Menu `Traffic` — Trái tim can thiệp, định tuyến & bắt gói tin

Menu `Traffic` chứa toàn bộ các tính năng cốt lõi làm nên sức mạnh vượt trội của Reqable trong việc kiểm soát, phân tích và can thiệp dòng dữ liệu mạng.

```
Traffic
 ├── Record                   [ Ctrl + G ]
 ├── SSL Proxying             [ Ctrl + Alt + P ]
 ├── Mirror >                 [ Toggle: Shift + Ctrl + M | New: Shift + Alt + M | List: Alt + M ]
 ├── Gateway >                [ Toggle: Shift + Ctrl + G | New: Shift + Alt + G | List: Alt + G ]
 ├── Rewrite >                [ Toggle: Shift + Ctrl + K | New: Shift + Alt + K | List: Alt + K ]
 ├── Breakpoint >             [ Toggle: Shift + Ctrl + B | New: Shift + Alt + B | List: Alt + B ]
 ├── Script >                 [ Toggle: Shift + Ctrl + P | New: Shift + Alt + P | List: Alt + P ]
 ├── Reverse Proxy >          (Transparent Port Forwarding)
 ├── Access Control >         (IP Whitelist / Blacklist)
 ├── Network Throttling >     [ Alt + J ]
 ├── Report Server >          (Automated HAR Streaming)
 ├── Device >                 (Mobile Collaboration)
 ├── DNS Caching              (Local DNS Cache Switch)
 ├── Turbo Mode               [ F9 ]
 └── Incognito Mode           [ F10 ]
```

### Chi tiết các chức năng trong Menu `Traffic`:

1. **Record (`Ctrl + G`):** Công tắc chính bật/tắt việc ghi nhận và phân tích lưu lượng mạng (Live Capture). Khi tắt, gói tin vẫn đi qua proxy bình thường nhưng không được xử lý hay hiển thị trong danh sách, giúp tiết kiệm tài nguyên khi không cần debug.
2. **SSL Proxying (`Ctrl + Alt + P`):** Bảng cấu hình giải mã HTTPS (MITM):
   - **Intercept All:** Giải mã tất cả các kết nối SSL/TLS đi qua proxy.
   - **Bypass All:** Bỏ qua hoàn toàn giải mã SSL (kết nối HTTPS chỉ được hiển thị ở dạng đường hầm CONNECT có biểu tượng ổ khóa 🔒, không đọc được nội dung).
   - **Custom Rules:** Cấu hình danh sách tên miền chỉ định (hỗ trợ wildcard như `*.google.com`, `api.example.com*`) để chọn lọc tên miền nào cần Intercept hoặc Bypass.
   - **Hide Bypassed Traffic:** Tùy chọn ẩn hoàn toàn các gói tin SSL bị bypass khỏi danh sách để tránh làm loãng màn hình log.
   - **SSL Certificates:** Quản lý nạp Client Certificate (phục vụ mTLS) hoặc Server Certificate (phục vụ bypass SSL Pinning).
3. **Mirror:** Tính năng ánh xạ và chuyển hướng cấp độ Host (tương tự như sửa file hosts của hệ điều hành nhưng linh hoạt và tức thời hơn). Cho phép chuyển hướng toàn bộ traffic gửi tới Host A sang Host B (ví dụ chuyển từ `api.production.com` sang máy chủ nội bộ `api.dev.local:8080`), hỗ trợ tùy chọn giữ nguyên hoặc ghi đè Header `Host`, `SNI` và `Certificate CN`.
4. **Gateway:** Bộ kiểm soát chính sách mạng phân tầng theo mô hình OSI:
   - **Tầng Mạng (Network Layer - L4):** Áp dụng theo Domain hoặc IP/CIDR. Gồm 3 chế độ: *Allow Only* (chỉ cho phép traffic khớp xuất hiện trong danh sách), *Bypass* (bỏ qua proxy), và *Block* (chặn đứng kết nối TCP ở mức socket).
   - **Tầng Ứng Dụng (Application Layer - L7):** Áp dụng theo Domain, IP, HTTP, WebSocket. Gồm 6 chế độ: *Allow Only*, *Bypass*, *Block Outbound* (chặn chiều gửi lên server), *Block Inbound* (chặn chiều trả về client), *Suspend Outbound* (treo kết nối chiều gửi để giả lập timeout phía client), và *Suspend Inbound* (treo kết nối chiều nhận để giả lập timeout phía server).
5. **Rewrite:** Cơ chế tự động can thiệp và sửa đổi dữ liệu theo bộ quy tắc định sẵn (sẽ được phân tích sâu ở Chương 3).
6. **Breakpoint:** Điểm dừng can thiệp luồng dữ liệu thời gian thực (Real-time Interception), cho phép người dùng dừng gói tin lại để kiểm tra và chỉnh sửa trước khi cho đi tiếp.
7. **Script:** Tính năng lập trình can thiệp luồng dữ liệu bằng ngôn ngữ **Python 3**, cho phép xử lý các bài toán logic phức tạp như giải mã mã hóa đối xứng, tính toán chữ ký số HMAC, hoặc ghi dữ liệu ra cơ sở dữ liệu bên ngoài.
8. **Reverse Proxy:** Tạo máy chủ proxy ngược cục bộ trên một cổng xác định (ví dụ 9001) và chuyển tiếp trong suốt đến máy chủ đích thực tế. Hữu ích khi ứng dụng không hỗ trợ cấu hình proxy hoặc thiết bị không thể cài chứng chỉ CA.
9. **Access Control:** Quản lý danh sách các địa chỉ IP Client được phép kết nối vào Proxy Reqable:
   - *Allow Mode (Whitelist):* Chỉ cho phép các IP/dải mạng xác định (hỗ trợ IPv4, IPv6, ký tự đại diện `*`, `?`) được kết nối.
   - *Disallow Mode (Blacklist):* Chặn các IP không mong muốn để tránh làm bẩn danh sách gói tin hoặc ngăn chặn các vòng lặp mạng.
10. **Network Throttling (`Alt + J`):** Giả lập băng thông mạng (Băng thông Uplink/Downlink, Độ trễ Latency, Tỉ lệ rớt gói Packet Loss Rate).
11. **Report Server:** Tự động xuất các phiên HTTP đã hoàn thành thành định dạng chuẩn HAR JSON và truyền dữ liệu thời gian thực (streaming) qua HTTP POST về một máy chủ phân tích tập trung.
12. **Device:** Quản lý các thiết bị di động tham gia phiên debug cùng Reqable Desktop qua mã QR hoặc địa chỉ IP.
13. **DNS Caching:** Bật/tắt bộ nhớ đệm phân giải DNS nội bộ của Reqable để tăng tốc độ phân giải tên miền và giảm số lượng truy vấn DNS ra ngoài hệ thống mạng.
14. **Turbo Mode (`F9`):** Chế độ tăng tốc cực đại: Tạm dừng việc cập nhật giao diện danh sách gói tin (Traffic List UI), nhưng các rule Gateway, Mirror, Rewrite, Script vẫn chạy ngầm với hiệu năng tối đa. Giúp máy tính không bị treo hoặc tràn RAM khi chịu tải hàng triệu request.
15. **Incognito Mode (`F10`):** Chế độ ẩn danh: Tuyệt đối không lưu dữ liệu gói tin tạm xuống ổ cứng (chỉ lưu trữ trên bộ nhớ RAM). Toàn bộ dữ liệu phiên sẽ biến mất hoàn toàn ngay khi người dùng đóng ứng dụng.

---

## 2.5. Menu `Proxy` — Cấu hình cổng mạng, giao thức & định tuyến ra ngoài

Menu `Proxy` điều khiển các thiết lập tầng mạng, quản lý việc chiếm quyền proxy hệ điều hành và thiết lập chuỗi proxy trung gian.

| Mục Menu | Phím Tắt | Phân Loại | Chức Năng Chi Tiết & Thông Số Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| **System Proxy** | `F12` | Checkbox / Toggle | Bật/Tắt thiết lập Reqable làm proxy mặc định của hệ điều hành Windows (tự động điền IP `127.0.0.1` và Port `9000` vào Windows Internet Settings). Biểu tượng chấm tròn trên Toolbar sẽ chuyển sang màu xanh lá khi đang kích hoạt, hoặc màu vàng khi tắt. |
| **Auto Override** | *Không* | Checkbox / Toggle | Tự động giám sát và ghi đè lại cài đặt System Proxy: Nếu phát hiện có phần mềm khác (như VPN, Clash, v2ray, Fiddler) cố tình can thiệp hoặc thay đổi proxy hệ thống khi Reqable đang chạy, Reqable sẽ lập tức giật lại quyền kiểm soát proxy. |
| **Modify Port** | *Không* | Dialog Action | Thay đổi cổng lắng nghe của proxy server Reqable (mặc định là cổng `9000`). Nếu cổng này bị ứng dụng khác chiếm dụng, Reqable sẽ cảnh báo hoặc tự động tìm kiếm cổng kế tiếp còn trống. |
| **Web Proxy** | *Không* | Radio Checkbox | Thiết lập chế độ proxy web truyền thống (HTTP / HTTPS). Đây là chế độ mặc định trên hệ điều hành Windows. |
| **Socks Proxy** | *Không* | Radio Checkbox | Chuyển proxy hệ thống sang giao thức SOCKS (hỗ trợ SOCKS4, SOCKS4a, SOCKS5). Hỗ trợ đầy đủ lưu lượng UDP qua SOCKS5 (tự động chặn các gói HTTP/3 QUIC qua UDP để ép client fallback về giao thức TCP TLS). |
| **Proxy Pattern >** | *Không* | Submenu | Tùy chọn định dạng chuỗi thiết lập System Proxy trên Windows để tương thích với các ứng dụng client đặc thù:<br>1. `{ip}:{http_port}` (chuẩn mặc định của Windows).<br>2. `http=http://{ip}:{http_port};https=http://{ip}:{http_port}`<br>3. `http={ip}:{http_port};https={ip}:{http_port}` |
| **Loopback** | *Không* | Checkbox / Toggle | Bật/tắt khả năng bắt gói tin cục bộ gửi tới `localhost` / `127.0.0.1` trên Windows. Giúp các lập trình viên backend/frontend dễ dàng debug các API nội bộ đang chạy trên máy dev. |
| **Secondary Proxy >** | *Không* | Submenu | Cấu hình **Proxy Thứ Cấp (Upstream Proxy)**: Khi Reqable tiếp nhận một request, nó sẽ không gửi trực tiếp ra Internet mà chuyển tiếp tới một máy chủ proxy trung gian khác (ví dụ proxy doanh nghiệp của công ty hoặc client VPN Shadowsocks/Clash).<br>- Hỗ trợ 2 chế độ lọc: **Include Mode** (chỉ các tên miền chỉ định mới đi qua secondary proxy) và **Exclude Mode** (các tên miền chỉ định sẽ đi thẳng, bỏ qua secondary proxy). |

---

## 2.6. Menu `Certificate` — Quản lý chứng chỉ Root CA & SSL tùy biến

Menu `Certificate` cung cấp các công cụ thiết yếu để quản trị chứng chỉ số, chìa khóa để giải mã lưu lượng HTTPS trên máy tính và các thiết bị di động.

1. **Install CA Certificate on this Device:** Hướng dẫn và tự động cài đặt chứng chỉ Root CA của Reqable vào kho chứng chỉ của hệ điều hành hiện tại (Windows Certificate Manager: *Trusted Root Certification Authorities*). Hỗ trợ cài đặt tự động 1-click hoặc hướng dẫn cài đặt thủ công.
2. **Install Certificate on Mobile Device:** Cung cấp giải pháp nạp chứng chỉ cho thiết bị di động:
   - **Android:** Hướng dẫn cài đặt User Certificate hoặc System Certificate (hỗ trợ cài tự động 1-click qua ADB cho máy đã ROOT, xuất module Magisk, hoặc hướng dẫn tích hợp thư viện `user-certificate-trust` vào source code).
   - **iOS:** Tải cấu hình chứng chỉ `.mobileconfig` thông qua trình duyệt Safari, sau đó hướng dẫn vào *Settings -> General -> Profile Downloaded* để cài đặt, và kích hoạt tin cậy tại *Settings -> General -> About -> Certificate Trust Settings*.
3. **CA Certificate Management:**
   - **Export CA Certificate:** Xuất chứng chỉ CA gốc ra các định dạng chuẩn: `.crt`, `.cer`, hoặc `.p12` (chứa cả cặp khóa riêng Private Key có mã hóa mật khẩu).
   - **Import CA Certificate:** Cho phép người dùng nhập một chứng chỉ CA có sẵn từ Charles Proxy hoặc Fiddler (.p12) vào Reqable để tái sử dụng trên toàn bộ các thiết bị thử nghiệm mà không cần phải cài lại cert mới trên điện thoại.
   - **Reset CA Certificate:** Tạo mới hoàn toàn cặp khóa Root CA của Reqable. Toàn bộ các thiết bị trước đó sẽ cần phải cài lại cert mới sau khi reset.
4. **Custom SSL Certificates:**
   - **Client Certificate:** Cấu hình chứng chỉ người dùng gửi lên server để phục vụ xác thực hai chiều (**mTLS / Two-Way SSL**). Hỗ trợ nạp file `.p12` / `.pfx` kèm mật khẩu mở khóa.
   - **Server Certificate:** Nạp chứng chỉ gốc hợp lệ của máy chủ để vượt qua các cơ chế kiểm tra **SSL Pinning** mà không cần sửa đổi mã nguồn ứng dụng client.

---

## 2.7. Menu `Help` — Tài liệu, kiểm tra cập nhật & cộng đồng

- **Getting Started:** Mở hướng dẫn tổng quan từng bước dành cho người mới bắt đầu.
- **Documentation:** Mở trực tiếp trang tài liệu kỹ thuật trực tuyến của Reqable (`https://reqable.com/docs`).
- **Check for Updates:** Kết nối máy chủ Reqable để kiểm tra phiên bản mới và tự động cập nhật.
- **Feedback / Community:** Cung cấp liên kết đến kho mã nguồn GitHub Issues, cộng đồng Discord, kênh Twitter/X và Telegram.
- **About Reqable:** Hiển thị số hiệu phiên bản ứng dụng, trạng thái bản quyền (Community Edition / Professional License), và thông tin nhà phát triển.

---

## 2.8. Ma trận tra cứu phím tắt toàn năng (Comprehensive Shortcuts Matrix)

Bảng tổng hợp tra cứu nhanh toàn bộ hệ thống phím tắt trên Reqable Desktop:

| Phím Tắt | Phân Vùng / Phạm Vi | Chức Năng Thực Thi Chi Tiết |
| :--- | :--- | :--- |
| `Ctrl + T` | Tabs | Mở một tab kiểm thử HTTP REST API mới |
| `Ctrl + W` | Tabs / Windows | Đóng tab làm việc hoặc đóng cửa sổ con (Sub-window) |
| `Shift + Ctrl + W` | Tabs | Đóng toàn bộ các tab đang mở |
| `Ctrl + 1` .. `9` | Tabs | Chuyển con trỏ làm việc tới tab có thứ tự từ 1 đến 9 |
| `Ctrl + 0` | Tabs | Chuyển nhanh tới tab cuối cùng trên thanh tab bar |
| `Ctrl + [` / `]` | Tabs | Chuyển tab sang bên trái / bên phải |
| `F1` | View Sidebar | Mở hoặc đóng thanh Explorer (Cây cấu trúc Domain/App) |
| `F2` | View Sidebar | Mở hoặc đóng thanh Collection (Bộ sưu tập API) |
| `F3` | View Sidebar | Mở hoặc đóng thanh Environment (Biến môi trường) |
| `F4` | View Sidebar | Mở hoặc đóng thanh History (Lịch sử bắt gói và gửi API) |
| `F5` | View Sidebar | Mở hoặc đóng thanh Device (Danh sách thiết bị kết nối) |
| `F6` | View Sidebar | Mở hoặc đóng thanh Toolbox (Bộ công cụ mini) |
| `Shift + Ctrl + [` | View Layout | Mở rộng hoặc thu gọn thanh Sidebar bên trái |
| `Shift + Ctrl + ]` | View Layout | Chuyển đổi bố cục hiển thị dọc/ngang (Vertical/Horizontal) |
| `Shift + Ctrl + \` | View Layout | Bật/Tắt chế độ tập trung toàn màn hình (Zen Mode) |
| `Ctrl + =` / `Ctrl + -` | View Zoom | Phóng to (Zoom In) / Thu nhỏ (Zoom Out) giao diện |
| `Ctrl + G` | Traffic | Bắt đầu hoặc tạm dừng ghi nhận lưu lượng mạng (Record) |
| `F12` | Proxy | Kích hoạt hoặc hủy kích hoạt System Network Proxy |
| `F9` | Traffic | Bật/Tắt chế độ Turbo Mode (Tối đa hóa hiệu năng proxy) |
| `F10` | Traffic | Bật/Tắt chế độ Ẩn danh (Incognito Mode - Không lưu disk) |
| `Ctrl + Alt + P` | Traffic | Mở hộp thoại cấu hình SSL Proxying (Bypass/Intercept) |
| `Shift + Ctrl + M` | Traffic Mirror | Bật / Tắt tính năng Mirror |
| `Shift + Alt + M` | Traffic Mirror | Tạo mới một quy tắc Mirror |
| `Alt + M` | Traffic Mirror | Mở danh sách quản lý các quy tắc Mirror |
| `Shift + Ctrl + G` | Traffic Gateway | Bật / Tắt tính năng Gateway |
| `Shift + Alt + G` | Traffic Gateway | Tạo mới một quy tắc Gateway |
| `Alt + G` | Traffic Gateway | Mở danh sách quản lý các quy tắc Gateway |
| `Shift + Ctrl + K` | Traffic Rewrite | Bật / Tắt tính năng Rewrite |
| `Shift + Alt + K` | Traffic Rewrite | Tạo mới một quy tắc Rewrite |
| `Alt + K` | Traffic Rewrite | Mở danh sách quản lý các quy tắc Rewrite |
| `Shift + Ctrl + B` | Traffic Breakpoint| Bật / Tắt tính năng Breakpoint |
| `Shift + Alt + B` | Traffic Breakpoint| Tạo mới một quy tắc Breakpoint |
| `Alt + B` | Traffic Breakpoint| Mở danh sách quản lý các quy tắc Breakpoint |
| `Shift + Ctrl + P` | Tools / Script | Mở Command Palette / Bật Tắt tính năng Python Script |
| `Shift + Alt + P` | Traffic Script | Tạo mới một quy tắc Python Script |
| `Alt + P` | Traffic Script | Mở danh sách quản lý các quy tắc Python Script |
| `Alt + T` | Tools | Khởi chạy Proxy Terminal (đã inject sẵn CA và biến môi trường) |
| `Alt + J` | Tools / Traffic | Mở bảng cấu hình Network Throttling |
| `Shift + Ctrl + R` | Traffic / Testing | Xóa sạch bảng danh sách traffic / Reset tab kiểm thử |
| `Ctrl + F` | Traffic / Viewer | Mở thanh công cụ tìm kiếm dữ liệu (Search Panel) |
| `Ctrl + C` | Traffic List | Sao chép đường dẫn URL của request đang chọn |
| `Shift + Ctrl + C` | Traffic List | Sao chép lệnh cURL của request đang chọn vào clipboard |
| `Shift + Ctrl + I` | API Testing | Nhập lệnh cURL từ bộ nhớ tạm vào tab API hiện tại |
| `Shift + Ctrl + E` | API Testing | Xuất yêu cầu API hiện tại thành câu lệnh cURL |
| `Ctrl + Enter` | API / Traffic | Gửi yêu cầu API / Lặp lại (Repeat) request trong traffic list |
| `Shift + Ctrl + Enter`| Traffic List | Soạn lại và chỉnh sửa yêu cầu (Edit & Compose request) |
| `Ctrl + I` | Traffic List | Lưu request đang chọn từ traffic list vào API Collection |
| `Ctrl + L` | Traffic List | Định vị con trỏ tới dòng đang được chọn |
| `Ctrl + Y` | Traffic List | Mở cửa sổ so sánh (Diff) hai phiên HTTP đang chọn |
| `Shift + Ctrl + Y` | Traffic List | Thêm request vào danh sách chờ so sánh (Diff Pool) |
| `Alt + 1` .. `5` | Traffic List | Đổi màu đánh dấu (Highlight): Đỏ, Vàng, Xanh lá, Xanh dương, Xám |
| `Alt + -` | Traffic List | Đánh dấu gạch ngang (Strikethrough) dòng đang chọn |
| `Alt + 0` | Traffic List | Xóa bỏ toàn bộ màu đánh dấu trên dòng đang chọn |
| `Alt + C` | API Testing | Bật / Tắt chế độ tự động quản lý Cookie (Auto-Cookie Jar) |
| `Alt + H` | API Testing | Bật / Tắt tự động lưu lịch sử API (Auto-Save History) |
| `Alt + I` | API Testing | Bật / Tắt việc tự động gán header định danh Reqable ID |

---

# 3. CHUYÊN SÂU TÍNH NĂNG TRAFFIC MANIPULATION

Khả năng can thiệp lưu lượng (Traffic Manipulation) là vũ khí lợi hại nhất của một HTTP Proxy trong quá trình kiểm thử phần mềm, pentest bảo mật và kỹ thuật dịch ngược (Reverse Engineering). Reqable cung cấp 6 phân hệ can thiệp mạnh mẽ:

## 3.1. Rewrite Rules — 5 chế độ can thiệp tự động

Khác với Charles Proxy chia thành nhiều công cụ riêng biệt (Map Remote, Map Local, Rewrite), Reqable quy chuẩn toàn bộ vào một phân hệ **Rewrite** duy nhất với 5 chế độ hoạt động chuyên biệt:

```
                            REWRITE PIPELINE
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       ▼                           ▼                           ▼
[1. Redirection]           [2. Replace Request]        [3. Replace Response]
(Map Remote / Path)        (Replace whole req)         (Mock Status/Body)
                                   │                           │
                                   ▼                           ▼
                          [4. Modify Request]         [5. Modify Response]
                          (Headers/Query/Regex)       (Headers/Status/Regex)
```

1. **Chế độ 1: Redirection (Map Remote):**
   - Chuyển hướng lưu lượng từ URL này sang URL khác.
   - Hỗ trợ ký tự đại diện directory matching: `https://api.prod.com/v1/*` $\to$ `https://api.staging.internal/v1/$1`.
2. **Chế độ 2: Replace Request:**
   - Thay thế toàn bộ bản tin Request gửi lên server.
   - Cho phép ghi đè hoàn toàn: Method (ví dụ đổi GET thành POST), Đường dẫn Path, danh sách Headers và nội dung Body (Text, nạp từ File cục bộ hoặc xóa rỗng).
3. **Chế độ 3: Replace Response (Mocking):**
   - Chặn đứng gói tin tại proxy và trả về dữ liệu giả lập (Mock) ngay lập tức mà không cần gửi request tới máy chủ thật.
   - Cực kỳ hữu dụng khi lập trình viên Frontend cần dữ liệu test khi Backend chưa viết xong API, hoặc kiểm thử các mã trạng thái biên (Status Code `500 Internal Server Error`, `403 Forbidden`, `429 Too Many Requests`).
4. **Chế độ 4: Modify Request:**
   - Can thiệp tinh tế vào các thành phần của Request:
     - Thêm, sửa, hoặc xóa một Query Parameter.
     - Bổ sung hoặc ghi đè Header (ví dụ tiêm header `Authorization: Bearer mock_token`).
     - Sửa đổi nội dung Body dạng chuỗi bằng biểu thức chính quy (Regex). Hỗ trợ toán tử thay thế nhóm `$1`, `$2`.
5. **Chế độ 5: Modify Response:**
   - Tương tự như Modify Request nhưng áp dụng cho dữ liệu phản hồi từ máy chủ:
     - Thay đổi mã trạng thái HTTP (ví dụ sửa từ 401 thành 200).
     - Ghi đè hoặc thêm Response Headers (ví dụ sửa header `Access-Control-Allow-Origin: *` để kiểm thử lỗi CORS).
     - Tìm và thay thế các chuỗi ký tự trong JSON response bằng Regex.

---

## 3.2. Breakpoint Rules — Can thiệp và chỉnh sửa dữ liệu thời gian thực

Khi cần kiểm thử các lỗ hổng logic (Business Logic Flaws) hoặc can thiệp thông số thanh toán mà không muốn viết quy tắc tự động cố định, **Breakpoint** là công cụ số một.

### Quy trình hoạt động thời gian thực (Interception Flow):
1. **Thiết lập quy tắc:** Kích hoạt Breakpoint (`Shift + Ctrl + B`), thêm rule chỉ định URL mục tiêu (ví dụ `https://shop.example.com/api/order/checkout`). Người dùng có thể chọn dừng ở chiều **Request**, chiều **Response**, hoặc **Cả hai**.
2. **Kích hoạt điểm dừng:** Khi ứng dụng client gửi request khớp điều kiện:
   - Reqable lập tức đóng băng (freeze) luồng mạng.
   - Cửa sổ **Breakpoint Executor** tự động bật lên hiển thị toàn bộ nội dung gói tin.
3. **Thao tác can thiệp:**
   - Kỹ sư có thể chuyển sang chế độ GUI hoặc Raw để sửa đổi: giá tiền sản phẩm, ID người dùng, số lượng hàng, headers...
4. **Điều khiển tiếp tục:**
   - Nhấp nút **Execute:** Gửi gói tin đã chỉnh sửa đi tiếp tới đích.
   - Nhấp nút **Break:** Lập tức hủy bỏ kết nối, trả về lỗi kết nối mạng cho client.

---

## 3.3. Mirror Rules — Ánh xạ tên miền và chuyển hướng Host

Mirror hoạt động ở tầng vận chuyển tên miền (DNS/Host redirection):
- Ánh xạ toàn bộ các yêu cầu từ một tên miền nguồn sang tên miền đích (ví dụ ánh xạ `*.api.company.com` sang máy chủ nội bộ `192.168.1.50:8080`).
- **Tùy chọn nâng cao:**
  - *Preserve Host Header:* Giữ nguyên tiêu đề Host ban đầu của client gửi lên, hữu dụng khi máy chủ đích yêu cầu Virtual Hosting.
  - *Preserve SNI:* Giữ nguyên Server Name Indication trong quá trình bắt tay SSL.

---

## 3.4. Gateway Rules — Kiểm soát lưu lượng L4 (Network) và L7 (Application)

Khác với các proxy thông thường chỉ lọc theo URL, Gateway của Reqable cho phép thiết lập chính sách kiểm soát lưu lượng chuyên nghiệp phân tách theo mô hình OSI:

### Tầng 4: Network Layer
Áp dụng theo địa chỉ IP, dải mạng CIDR (ví dụ `10.0.0.0/8`), hoặc Domain:
- **Allow Only:** Chế độ danh sách trắng — chỉ các kết nối khớp quy tắc mới được hiển thị và xử lý, toàn bộ kết nối khác bị bỏ qua.
- **Bypass:** Cho phép kết nối đi thẳng qua proxy mà không can thiệp giải mã SSL.
- **Block:** Chặn đứng hoàn toàn kết nối ở mức socket TCP (từ chối bắt tay TCP).

### Tầng 7: Application Layer
Áp dụng theo Domain, IP, giao thức HTTP hoặc WebSocket:
- **Block Outbound:** Chặn kết nối ngay khi client chuẩn bị gửi request lên máy chủ.
- **Block Inbound:** Cho phép gửi request lên máy chủ thành công, nhưng chặn đứng dữ liệu response khi máy chủ trả về cho client.
- **Suspend Outbound:** Giữ kết nối ở trạng thái treo vô thời hạn ở chiều gửi để giả lập lỗi nghẽn mạng hoặc timeout phía client (`Client Read Timeout`).
- **Suspend Inbound:** Giữ kết nối ở trạng thái treo ở chiều nhận để giả lập tình trạng máy chủ xử lý quá tải (`Gateway Timeout 504`).

---

## 3.5. Reverse Proxy — Cầu nối trong suốt bypass cài đặt chứng chỉ

Trong các môi trường kiểm thử bị khóa chặt (Kiosk devices, Smart TV, Apple Watch, máy ATM, thiết bị MDM của doanh nghiệp) nơi kỹ sư **hoàn toàn không thể cài đặt chứng chỉ Root CA vào thiết bị**, tính năng Reverse Proxy của Reqable là cứu tinh duy nhất:
- Reqable mở một cổng HTTP thông thường (ví dụ cổng `9001`) lắng nghe kết nối từ mạng cục bộ.
- Kỹ sư cấu hình thiết bị trỏ Base URL về `http://<IP_MAY_TINH_REQABLE>:9001`.
- **Cơ chế vận hành:**
  - Thiết bị kết nối tới Reqable bằng giao thức HTTP thuần không mã hóa, do đó **không cần cài đặt bất kỳ chứng chỉ SSL nào**.
  - Reqable tiếp nhận gói tin, hiển thị đầy đủ trên màn hình, hỗ trợ toàn bộ các quy tắc Rewrite/Breakpoint/Script, sau đó Reqable tự động thiết lập kết nối mã hóa HTTPS an toàn với máy chủ đích thực tế trên Internet.

---

## 3.6. Network Throttling — Giả lập điều kiện mạng thực tế và Chaos Testing

Giúp lập trình viên kiểm thử khả năng chịu lỗi và trải nghiệm người dùng của ứng dụng khi hoạt động trong các điều kiện mạng khắc nghiệt:
- **Băng thông (Bandwidth):** Giới hạn tốc độ tải lên (Upload) và tải xuống (Download) tính theo Kbps hoặc Mbps.
- **Độ trễ (Latency):** Bổ sung độ trễ giả lập (Delay) tính bằng mili-giây (ms).
- **Tỉ lệ rớt gói (Packet Loss):** Giả lập tỉ lệ mất gói tin ngẫu nhiên từ 0% đến 100%.

### Các cấu hình mẫu chuẩn tích hợp sẵn:
- **Offline:** Ngắt kết nối mạng hoàn toàn.
- **Bad Network:** Độ trễ 1000ms, tỉ lệ rớt gói 10%.
- **2G / 3G / 4G / 5G:** Giả lập băng thông và độ trễ chuẩn viễn thông.
- **Wi-Fi:** Giả lập mạng không dây tốc độ cao với jitter thấp.

---

# 4. PYTHON SCRIPTING TOÀN DIỆN

Tính năng **Python Script** là công cụ mạnh mẽ và linh hoạt nhất trong Reqable, đưa khả năng can thiệp lưu lượng vượt xa khỏi các biểu thức tĩnh của Rewrite hay thao tác thủ công của Breakpoint.

## 4.1. Kiến trúc IPC Subprocess và vòng đời Request/Response

Cơ chế thực thi kịch bản Python trong Reqable được thiết kế theo mô hình Inter-Process Communication (IPC) an toàn và độc lập:

```
[Reqable Core (C++)] ── Fork Subprocess ──> python main.py <type> <temp_file.json>
         │                                                        │
         │                                              [Parse JSON to Models]
         │                                                        │
         │                                              [Execute User Callback]
         │                                             (onRequest / onResponse)
         │                                                        │
         │                                              [Serialize to .cb file]
         │                                                        │
[Apply Modified Packet] <── Read .cb File ────────────────────────┘
```

1. Khi một gói tin mạng được chặn lại, Reqable trích xuất dữ liệu thành một file JSON tạm thời.
2. Reqable khởi chạy một tiến trình Python độc lập gọi `python main.py <type> <temp_file.json>`, trong đó `<type>` là `request` hoặc `response`.
3. Framework của Reqable nạp dữ liệu vào các lớp đối tượng (`Context`, `HttpRequest`, `HttpResponse`), sau đó gọi hàm callback tương ứng do người dùng viết:
   - `onRequest(context, request)`: Can thiệp trước khi request được gửi tới máy chủ.
   - `onResponse(context, response)`: Can thiệp trước khi response được trả về client.
4. **Hành vi ngắt kết nối (Connection Abort):** Nếu hàm callback trả về `None`, Reqable sẽ lập tức ngắt bỏ kết nối HTTP đó, đóng vai trò như một Web Application Firewall (WAF) mini.
5. **Độc lập tiến trình:** Cần ghi nhớ rằng `onRequest` và `onResponse` chạy ở **hai tiến trình Python hoàn toàn khác nhau**. Các biến toàn cục trong Python sẽ bị xóa sạch giữa hai chiều. Dữ liệu cần truyền giữa hai hàm bắt buộc phải lưu qua thuộc tính `context.shared`.

---

## 4.2. Khảo sát chi tiết mô hình dữ liệu (Data Models API)

Các lớp đối tượng được định nghĩa trong thư viện `reqable`:

### 1. Lớp `Context`
Đại diện cho siêu dữ liệu của phiên HTTP:
- `context.url` (`str`): URL đầy đủ của phiên làm việc.
- `context.scheme` (`str`): Giao thức (`http` hoặc `https`).
- `context.host` (`str`): Tên miền máy chủ đích.
- `context.port` (`int`): Cổng kết nối mạng.
- `context.id` (`int`): ID định danh số của gói tin trong danh sách bắt gói.
- `context.timestamp` (`int`): Thời điểm bắt đầu phiên HTTP (epoch milliseconds).
- `context.connection` (`Connection`): Thông tin IP/Port của Local và Remote socket.
- `context.app` (`App`): Tiến trình phát sinh yêu cầu (`app.name`, `app.id`, `app.path`).
- `context.highlight` (`Highlight`): Gán màu đánh dấu trên danh sách UI:
  `Highlight.none`, `Highlight.red`, `Highlight.yellow`, `Highlight.green`, `Highlight.blue`, `Highlight.teal`, `Highlight.strikethrough`.
- `context.comment` (`str`): Gán ghi chú văn bản trực tiếp lên dòng traffic.
- `context.env` (`dict`): Bộ biến môi trường của Reqable. Có thể đọc và ghi đè giá trị biến môi trường trong runtime.
- `context.shared` (`Any`): Biến chia sẻ trạng thái giữa `onRequest` và `onResponse`.

### 2. Lớp `HttpRequest`
- `request.method` (`str`): Phương thức (`GET`, `POST`, `PUT`, `DELETE`...).
- `request.path` (`str`): Đường dẫn tài nguyên (không gồm query).
- `request.protocol` (`str`): Giao thức (`HTTP/1.1`, `h2`).
- `request.queries` (`HttpQueries`): Danh sách tham số query string.
- `request.headers` (`HttpHeaders`): Danh sách HTTP Headers (không phân biệt hoa thường).
- `request.body` (`HttpBody`): Payload của yêu cầu.
- `request.contentType` (`str`): Tiêu đề `Content-Type`.
- `request.mime` (`str`): Kiểu MIME trích xuất từ Content-Type.

### 3. Lớp `HttpResponse`
- `response.request` (`HttpRequest`): Đối tượng request tương ứng của phản hồi.
- `response.code` (`int`): Mã trạng thái HTTP (dải 100 - 600).
- `response.message` (`str`): Thông điệp trạng thái (ví dụ `OK`).
- `response.headers` (`HttpHeaders`): Danh sách Headers phản hồi.
- `response.body` (`HttpBody`): Payload phản hồi từ máy chủ.

### 4. Lớp `HttpBody`
Quản lý dữ liệu thân của gói tin với 4 kiểu: None, Text, Binary, Multipart.
- `body.text('string')`: Gán chuỗi văn bản UTF-8.
- `body.binary(b'...bytes...')`: Gán mảng bytes nhị phân.
- `body.file('/path/to/file')`: Đọc dữ liệu từ file trên ổ đĩa nạp vào body.
- `body.jsonify()`: Chuyển đổi payload JSON thành đối tượng Python dictionary/list, cho phép truy cập và sửa đổi trực tiếp qua cú pháp `body['key'] = 'new_value'`.
- `body.replace(old, new)`: Tìm và thay thế chuỗi ký tự trong payload text.
- `body.writeFile('/path/to/output')`: Ghi nội dung body ra file cục bộ.

---

## 4.3. Cơ chế chia sẻ trạng thái liên tiến trình (`context.shared`)

Do hai hàm `onRequest` và `onResponse` chạy trong hai tiến trình độc lập, lập trình viên không thể sử dụng biến toàn cục (global variables). Thuộc tính `context.shared` được Reqable cung cấp để giải quyết bài toán này:

```python
from reqable import *
import time

def onRequest(context, request):
    # Lưu mốc thời gian bắt đầu gửi request và token xác thực vào context.shared
    context.shared = {
        'start_time': time.time(),
        'auth_token': request.headers['Authorization'] or 'None'
    }
    return request

def onResponse(context, response):
    # Đọc lại dữ liệu đã lưu từ onRequest
    shared_data = context.shared
    elapsed = time.time() - shared_data['start_time']
    print(f"Phiên {context.id} xử lý mất: {elapsed:.3f} giây. Token sử dụng: {shared_data['auth_token']}")
    return response
```

---

## 4.4. Bộ 5 mẫu kịch bản Python thực chiến hoàn chỉnh

Dưới đây là 5 mẫu script hoàn chỉnh được chuẩn hóa từ kho template của Reqable, sẵn sàng sử dụng trong các tình huống thực tế:

### Template 1: Mã hóa AES-CBC Payload với PKCS#7 Padding (`aes_encryption.py`)
Áp dụng khi kiểm thử các API bảo mật cao yêu cầu mã hóa toàn bộ dữ liệu trước khi gửi lên máy chủ:

```python
from reqable import *
import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Khóa bí mật và Vector khởi tạo trích xuất từ ứng dụng
KEY = b'1234567812345678'
IV  = b'1234567812345678'

def encrypt_aes_cbc(plaintext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    return encryptor.update(padded_data) + encryptor.finalize()

def onRequest(context, request):
    if request.body.isText:
        raw_plaintext = request.body.payload.encode('utf-8')
        encrypted_bytes = encrypt_aes_cbc(raw_plaintext)
        # Gán lại payload thành chuỗi Base64
        request.body.text(base64.b64encode(encrypted_bytes).decode('utf-8'))
        request.headers['Content-Type'] = 'application/octet-stream'
        print(f"[Reqable] Đã mã hóa payload cho URL: {context.url}")
    return request

def onResponse(context, response):
    return response
```

### Template 2: Giải mã Response Body mã hóa AES (`aes_decryption.py`)
Tự động giải mã các phản hồi từ máy chủ bị mã hóa, giúp kỹ sư quan sát dữ liệu rõ ràng ngay trên màn hình Reqable:

```python
from reqable import *
import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

KEY = b'1234567812345678'
IV  = b'1234567812345678'

def decrypt_aes_cbc(ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(decrypted_data) + unpadder.finalize()

def onRequest(context, request):
    return request

def onResponse(context, response):
    if response.body.isText:
        try:
            # Giải mã chuỗi Base64 trả về từ server
            ciphertext = base64.b64decode(response.body.payload)
            plaintext = decrypt_aes_cbc(ciphertext).decode('utf-8')
            # Ghi đè lại body bằng dữ liệu rõ ràng
            response.body.text(plaintext)
            response.headers['Content-Type'] = 'application/json'
            context.highlight = Highlight.green
            print(f"[Reqable] Giải mã thành công phản hồi cho phiên: {context.id}")
        except Exception as err:
            context.highlight = Highlight.red
            print(f"[Reqable] Lỗi giải mã: {err}")
    return response
```

### Template 3: Ký số chuẩn Amazon AWS Signature v4 (`aws_signature.py`)
Tự động tính toán đầy đủ chữ ký đa tầng SigV4 của Amazon Web Services khi can thiệp vào các API S3 hoặc API Gateway:

```python
from reqable import *
import hmac
import hashlib
import datetime

ACCESS_KEY = 'AKIAEXAMPLE12345678'
SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
REGION     = 'us-east-1'
SERVICE    = 's3'

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    return sign(k_service, 'aws4_request')

def onRequest(context, request):
    method = request.method
    canonical_uri = request.path
    sorted_queries = sorted(request.queries)
    canonical_querystring = HttpQueries(sorted_queries).concat()

    # Tính băm Payload
    if request.body.isNone:
        payload_hash = hashlib.sha256(''.encode('utf-8')).hexdigest()
    elif request.body.isText:
        payload_hash = hashlib.sha256(request.body.payload.encode('utf-8')).hexdigest()
    elif request.body.isBinary:
        payload_hash = hashlib.sha256(request.body.payload).hexdigest()
    else:
        payload_hash = hashlib.sha256(''.encode('utf-8')).hexdigest()

    request.headers['x-amz-content-sha256'] = payload_hash

    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = now.strftime('%Y%m%d')
    request.headers['x-amz-date'] = amz_date

    # Chuẩn hóa Headers
    sorted_headers = sorted(request.headers)
    canonical_headers = f'host:{context.host}\n'
    signed_headers = 'host;'
    for header in sorted_headers:
        name, value = header.split(': ', 1)
        lower_name = name.lower().strip()
        if lower_name.startswith('x-amz-') or lower_name == 'content-type':
            canonical_headers += f"{lower_name}:{value.strip()}\n"
            signed_headers += f"{lower_name};"

    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    credential_scope = f"{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(SECRET_KEY, date_stamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    request.headers['Authorization'] = f"AWS4-HMAC-SHA256 Credential={ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return request

def onResponse(context, response):
    return response
```

### Template 4: Ký số Alibaba Cloud OSS Signature (`aliyun_oss_signature.py`)
Tính toán header `Authorization` cho dịch vụ lưu trữ đám mây Aliyun OSS:

```python
from reqable import *
import hmac
import hashlib
import base64
import datetime

OSS_ACCESS_KEY_ID = 'LTAI5tExampleKeyID'
OSS_ACCESS_KEY_SECRET = 'ExampleSecretKey123456789'

def onRequest(context, request):
    date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    bucket_name = context.host.split('.')[0]
    string_to_sign = f"{request.method}\n\n\n{date}\n/{bucket_name}{request.path}"
    
    signature = base64.b64encode(
        hmac.new(OSS_ACCESS_KEY_SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1).digest()
    ).decode('utf-8')

    request.headers['Date'] = date
    request.headers['Authorization'] = f"OSS {OSS_ACCESS_KEY_ID}:{signature}"
    return request

def onResponse(context, response):
    return response
```

### Template 5: Tự động ký băm MD5 cho Query Parameters (`md5_sign_for_query.py`)
Mẫu kinh điển chống can thiệp tham số trên ứng dụng di động:

```python
from reqable import *
import hashlib

SECRET_SALT = "MySecretSalt2026"

def onRequest(context, request):
    # Sắp xếp các tham số query theo thứ tự bảng chữ cái
    sorted_queries = sorted(request.queries)
    # Ghép chuỗi query chuẩn hóa
    base_query_string = HttpQueries(sorted_queries).concat()
    
    # Tính mã băm MD5 kèm muối bảo mật (Salt)
    hasher = hashlib.md5()
    hasher.update((base_query_string + SECRET_SALT).encode('utf-8'))
    signature = hasher.hexdigest()

    # Gán chữ ký vào Request Header hoặc Query
    request.headers['x-signature'] = signature
    context.comment = f"Re-signed MD5: {signature}"
    return request

def onResponse(context, response):
    return response
```

### *Bonus Template: Tự động trích xuất và lưu file ảnh từ Response (MIME Detection)*

```python
from reqable import *
from mimetypes import guess_extension
import datetime
import os

def onRequest(context, request):
    return request

def onResponse(context, response):
    mime = response.mime
    if mime and mime.startswith('image/'):
        save_dir = os.path.expanduser('~/Downloads/reqable_images/')
        os.makedirs(save_dir, exist_ok=True)
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ext = guess_extension(mime) or '.png'
        file_path = os.path.join(save_dir, filename + ext)
        
        response.body.writeFile(file_path)
        context.highlight = Highlight.yellow
        context.comment = f"Saved: {os.path.basename(file_path)}"
        print(f"[Reqable] Đã lưu ảnh: {file_path}")
    return response
```

---

# 5. REQABLE MCP SERVER & TÍCH HỢP AI AGENT

Reqable là công cụ proxy tiên phong trên thế giới hỗ trợ giao thức **Model Context Protocol (MCP)** của Anthropic. Tính năng này biến Reqable thành một trợ lý mạng có mắt thần cho các AI Agent (như Claude Desktop, Cursor IDE, Windsurf, Antigravity).

## 5.1. Kiến trúc kết nối Model Context Protocol (MCP) trong Reqable

Hệ thống MCP Server của Reqable được viết bằng ngôn ngữ **Dart** (`package:mcp_dart`) nằm trong repository gốc. Nó vận hành như một cầu nối thông minh:

```
+----------------+      JSON-RPC (stdio)      +--------------------+      HTTP REST (Local)     +--------------------+
|    AI AGENT    | ◄────────────────────────► | REQABLE MCP SERVER | ◄────────────────────────► |   REQABLE DESKTOP  |
| (Claude/Cursor)|                            |   (Dart Binary)    |                            | (C++ Proxy Engine) |
+----------------+                            +--------------------+                            +--------------------+
```

1. AI Agent kích hoạt tiến trình MCP Server qua luồng xuất nhập chuẩn (`stdio`).
2. Khi AI Agent cần kiểm tra mạng, nó phát ra một lệnh gọi công cụ MCP (Tool Call).
3. MCP Server nhận lệnh, dịch thành một HTTP REST request gửi tới máy chủ API nội bộ của Reqable Desktop (mặc định lắng nghe trên cổng 9000).
4. Reqable Desktop xử lý hành động (lọc log, tạo rewrite, sửa breakpoint) và trả kết quả JSON về cho MCP Server để nạp vào ngữ cảnh của AI.

---

## 5.2. Cấu hình MCP Server (`.mcp.json`) và phân quyền công cụ

Để tích hợp Reqable vào các môi trường AI (Claude Desktop, Cursor, Antigravity, Cline, v.v.), cấu hình file `.mcp.json` theo một trong hai phương thức sau:

### Phương thức 1: Sử dụng NPX (Khuyên dùng — Không cần cài đặt Dart SDK)
```json
{
  "mcpServers": {
    "reqable-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "reqable-mcp-server"
      ]
    }
  }
}
```

### Phương thức 2: Chạy trực tiếp từ mã nguồn Dart SDK
Sử dụng file điểm vào `bin/main.dart` của dự án:
```json
{
  "mcpServers": {
    "reqable-mcp": {
      "command": "dart",
      "args": [
        "run",
        "H:/reqble-mcp/bin/main.dart",
        "--host", "127.0.0.1",
        "--port", "9000",
        "--scope", "all"
      ]
    }
  }
}
```

Hoặc thực thi trực tiếp từ thư mục gốc của repository:
```bash
dart run bin/main.dart --host 127.0.0.1 --port 9000 --scope all
```

### Các cờ tham số (CLI Options):
- `--host`, `-h`: Địa chỉ máy chủ Reqable API (mặc định: `127.0.0.1`).
- `--port`, `-p`: Cổng API của Reqable (tự động phát hiện từ file `capture_config`, mặc định `9000`).
- `--token`, `-t`: Khóa xác thực truy cập API (nếu được thiết lập trong biến môi trường `REQABLE_TOKEN`).
- `--scope`, `-s`: Phạm vi công cụ đăng ký:
  - `minimal`: Chỉ mở các công cụ thiết yếu (lọc gói tin, đọc chi tiết, tạo cURL) nhằm tối ưu ngữ cảnh token.
  - `all`: Mở toàn bộ 146 công cụ quản trị chuyên sâu của hệ sinh thái Reqable.

---

## 5.3. Danh mục 146 công cụ MCP theo nhóm chức năng (Scope: all)

Khi khởi chạy với cờ `--scope all`, Reqable MCP Server cung cấp kho công cụ khổng lồ gồm **146 công cụ** chia thành 14 nhóm chức năng chuyên sâu:

1. **HTTP/REST, WebSocket, Raw & gRPC Testing (7 công cụ):**
   - `rest_http_create_from_url`: Tạo HTTP request kiểm thử từ URL.
   - `rest_http_create_from_curl`: Tạo HTTP request kiểm thử tự động từ chuỗi cURL.
   - `rest_http_update`: Cập nhật cấu hình HTTP test (headers, params, body).
   - `rest_raw_update`: Cập nhật cấu hình HTTP Raw request (chỉnh sửa trực tiếp raw socket stream).
   - `rest_grpc_update`: Cập nhật cấu hình kiểm thử gRPC request (service, method, payload).
   - `rest_websocket_create_from_url`: Tạo kết nối WebSocket kiểm thử từ URL.
   - `rest_websocket_update`: Cập nhật cấu hình phiên kết nối WebSocket.
2. **Environment Management (8 công cụ):**
   - `environment_list`: Lấy danh sách toàn bộ các môi trường biến.
   - `environment_get_by_id`: Lấy chi tiết biến và cấu hình theo Environment ID.
   - `environment_get_active`: Lấy thông tin môi trường hiện đang được kích hoạt (active).
   - `environment_create`: Tạo môi trường biến mới.
   - `environment_update`: Cập nhật biến số và giá trị trong môi trường.
   - `environment_delete`: Xóa môi trường biến theo ID.
   - `environment_select`: Kích hoạt một môi trường làm việc cụ thể.
   - `environment_builtin_variables`: Lấy danh sách các biến động tích hợp sẵn của hệ thống.
3. **Collection Management (16 công cụ):**
   - `collection_list`: Lấy danh sách toàn bộ Collections hiện có.
   - `collection_structure`: Xem toàn bộ cấu trúc cây phân cấp (folders, APIs) của Collection.
   - `collection_get`: Lấy chi tiết thông tin và metadata của một Collection.
   - `collection_create`: Tạo mới một Collection.
   - `collection_update`: Cập nhật tên hoặc thông tin Collection.
   - `collection_delete`: Xóa một Collection khỏi không gian làm việc.
   - `collection_folder_get`: Lấy thông tin chi tiết thư mục con trong Collection.
   - `collection_folder_create`: Tạo thư mục con mới trong Collection.
   - `collection_folder_update`: Đổi tên hoặc cập nhật thuộc tính thư mục con.
   - `collection_folder_delete`: Xóa thư mục con trong Collection.
   - `collection_api_get`: Lấy thông tin chi tiết một API request lưu trong Collection.
   - `collection_api_create`: Tạo API request mới trong Collection.
   - `collection_api_add`: Thêm API request vào một thư mục cụ thể của Collection.
   - `collection_api_update`: Cập nhật thông số kỹ thuật của API trong Collection.
   - `collection_api_delete`: Xóa API request khỏi Collection.
   - `collection_api_generate_curl`: Tạo câu lệnh cURL từ API request lưu trong Collection.
4. **Script Resources (2 công cụ):**
   - `script_framework`: Trả về toàn bộ khung mã nguồn Python framework chuẩn (`reqable.py`).
   - `script_template`: Trả về template mẫu chuẩn cho script Python.
5. **Proxy Control (1 công cụ):**
   - `proxy_set`: Bật hoặc tắt System Proxy của Reqable từ xa (`enabled: true/false`).
6. **Live Traffic Capture Control (8 công cụ):**
   - `capture_live_status`: Lấy trạng thái lắng nghe traffic hiện tại.
   - `capture_live_set_enabled`: Bắt đầu hoặc dừng tiến trình bắt gói tin thời gian thực.
   - `capture_live_filter`: Lọc danh sách request/response theo URL, method, status code.
   - `capture_live_get_by_id`: Lấy dữ liệu chi tiết toàn diện (headers, raw payload) theo ID giao dịch.
   - `capture_live_clear`: Xóa sạch toàn bộ lịch sử live capture trên giao diện.
   - `capture_live_generate_curl`: Xuất lệnh cURL từ gói tin đã bắt được.
   - `capture_live_compose`: Đưa traffic bắt được sang tab REST Editor để chỉnh sửa và phát lại.
   - `capture_live_collection_add`: Thêm gói tin trực tiếp vào một Collection có sẵn.
7. **Breakpoints Rules (11 công cụ):**
   - Quản trị cấu hình và quy tắc điểm dừng: `capture_breakpoint_get_config`, `capture_breakpoint_set_enabled`, `capture_breakpoint_list`, `capture_breakpoint_set_item_enabled`, `capture_breakpoint_get_by_id`, `capture_breakpoint_create`, `capture_breakpoint_create_folder`, `capture_breakpoint_delete`, `capture_breakpoint_delete_folder`, `capture_breakpoint_update`, `capture_breakpoint_update_folder_name`.
8. **Rewrite Rules (11 công cụ):**
   - Tự động thay đổi dữ liệu HTTP: `capture_rewrite_get_config`, `capture_rewrite_set_enabled`, `capture_rewrite_list`, `capture_rewrite_set_item_enabled`, `capture_rewrite_get_by_id`, `capture_rewrite_create`, `capture_rewrite_create_folder`, `capture_rewrite_delete`, `capture_rewrite_delete_folder`, `capture_rewrite_update`, `capture_rewrite_update_folder_name`.
9. **Capture Script Rules (11 công cụ):**
   - Can thiệp lưu lượng bằng Python scripting: `capture_script_get_config`, `capture_script_set_enabled`, `capture_script_list`, `capture_script_set_item_enabled`, `capture_script_get_by_id`, `capture_script_create`, `capture_script_create_folder`, `capture_script_delete`, `capture_script_delete_folder`, `capture_script_update`, `capture_script_update_folder_name`.
10. **Gateway Rules (11 công cụ):**
    - Điều hướng cổng và chuyển tiếp lưu lượng: `capture_gateway_get_config`, `capture_gateway_set_enabled`, `capture_gateway_list`, `capture_gateway_set_item_enabled`, `capture_gateway_get_by_id`, `capture_gateway_create`, `capture_gateway_create_folder`, `capture_gateway_delete`, `capture_gateway_delete_folder`, `capture_gateway_update`, `capture_gateway_update_folder_name`.
11. **Mirror Rules (11 công cụ):**
    - Nhân bản lưu lượng sang máy chủ kiểm thử: `capture_mirror_get_config`, `capture_mirror_set_enabled`, `capture_mirror_list`, `capture_mirror_set_item_enabled`, `capture_mirror_get_by_id`, `capture_mirror_create`, `capture_mirror_create_folder`, `capture_mirror_delete`, `capture_mirror_delete_folder`, `capture_mirror_update`, `capture_mirror_update_folder_name`.
12. **Reverse Proxy Rules (11 công cụ):**
    - Cấu hình máy chủ reverse proxy ảo: `capture_reverse_proxy_get_config`, `capture_reverse_proxy_set_enabled`, `capture_reverse_proxy_list`, `capture_reverse_proxy_set_item_enabled`, `capture_reverse_proxy_lookup`, `capture_reverse_proxy_create`, `capture_reverse_proxy_create_folder`, `capture_reverse_proxy_delete`, `capture_reverse_proxy_delete_folder`, `capture_reverse_proxy_update`, `capture_reverse_proxy_update_folder_name`.
13. **SSL Proxying Rules (7 công cụ):**
    - Quản lý danh sách giải mã SSL/TLS: `capture_ssl_proxying_get_config`, `capture_ssl_proxying_get_active`, `capture_ssl_proxying_lookup`, `capture_ssl_proxying_select`, `capture_ssl_proxying_create`, `capture_ssl_proxying_delete`, `capture_ssl_proxying_update`.
14. **Advanced Traffic Controls (31 công cụ):**
    - **Network Throttling (8 công cụ):** `capture_network_throttling_get_config`, `capture_network_throttling_set_enabled`, `capture_network_throttling_get_active`, `capture_network_throttling_lookup`, `capture_network_throttling_select`, `capture_network_throttling_create`, `capture_network_throttling_delete`, `capture_network_throttling_update` (giả lập giới hạn băng thông, độ trễ mạng).
    - **Secondary Proxy (8 công cụ):** `capture_secondary_proxy_get_config`, `capture_secondary_proxy_set_enabled`, `capture_secondary_proxy_get_active`, `capture_secondary_proxy_lookup`, `capture_secondary_proxy_select`, `capture_secondary_proxy_create`, `capture_secondary_proxy_delete`, `capture_secondary_proxy_update` (quản lý upstream proxy chuỗi).
    - **Access Control (8 công cụ):** `capture_access_control_get_config`, `capture_access_control_set_enabled`, `capture_access_control_get_active`, `capture_access_control_lookup`, `capture_access_control_select`, `capture_access_control_create`, `capture_access_control_delete`, `capture_access_control_update` (quản trị whitelist/blacklist IP và domain).
    - **Report Server (7 công cụ):** `capture_report_server_get_config`, `capture_report_server_set_enabled`, `capture_report_server_lookup`, `capture_report_server_set_item_enabled`, `capture_report_server_create`, `capture_report_server_delete`, `capture_report_server_update` (tự động đẩy log HAR JSON về máy chủ phân tích).

---

## 5.4. Bảng đối chiếu API REST nội bộ của Reqable

| Endpoint API Nội Bộ | HTTP Method | MCP Tool Ánh Xạ | Mô Tả Tác Vụ |
| :--- | :--- | :--- | :--- |
| `/script/framework` | GET | `script_framework` | Lấy mã nguồn Python framework chuẩn |
| `/script/template` | GET | `script_template` | Lấy code script mẫu chuẩn |
| `/capture/script/config` | GET | `capture_script_get_config` | Lấy danh sách toàn bộ các quy tắc script |
| `/capture/script/enable` | POST | `capture_script_set_enabled` | Kích hoạt hoặc vô hiệu hóa phân hệ script |
| `/capture/script/create` | POST | `capture_script_create` | Tạo mới một quy tắc Python script |
| `/capture/script/update` | POST | `capture_script_update` | Cập nhật nội dung mã script của một quy tắc |
| `/capture/script/delete` | POST | `capture_script_delete` | Xóa một quy tắc script theo ID |
| `/capture/live/traffic` | POST | `capture_live_filter` | Truy vấn và lọc danh sách traffic bắt được |
| `/capture/live/detail` | POST | `capture_live_get_by_id` | Lấy toàn bộ chi tiết (headers, body) theo ID |
| `/proxy/set` | POST | `proxy_set` | Bật/tắt System Proxy của Reqable |

---

## 5.5. Kịch bản phối hợp AI Agent tự động hóa điều tra và xử lý lỗi

Khi tích hợp với AI Agent, người dùng có thể thực hiện các câu lệnh tự nhiên phức tạp:

**Câu lệnh của người dùng:**  
> *"Reqable ơi, hãy kiểm tra 10 request gần nhất bị mã lỗi 500 của tên miền `api.mycompany.com`. Phân tích nguyên nhân lỗi trong response body, sau đó tự tạo một quy tắc Rewrite để mock dữ liệu thành công mã 200 cho endpoint bị lỗi đó."*

**Quy trình AI Agent thực thi tự động:**
1. AI gọi `capture_live_filter` với tham số `{"host": "api.mycompany.com", "status": [500]}` để lấy danh sách ID gói tin lỗi.
2. AI gọi `capture_live_get_by_id` để đọc chi tiết headers và payload trả về của gói tin lỗi.
3. AI phân tích nguyên nhân lỗi (ví dụ thiếu trường `account_tier`).
4. AI gọi `capture_rewrite_create` với chế độ `Replace Response`, nạp payload JSON đã bổ sung trường `account_tier` và đặt `statusCode = 200`.
5. AI thông báo lại cho người dùng: *"Đã hoàn thành! Quy tắc Rewrite đã được áp dụng, ứng dụng của bạn hiện đã nhận được phản hồi thành công."*

---

# 6. ANDROID TRAFFIC CAPTURE & SSL PINNING BYPASS

Bắt gói tin và giải mã HTTPS trên hệ điều hành Android là bài toán phức tạp nhất trong quá trình reverse engineering do các lớp phòng vệ nghiêm ngặt của Google.

## 6.1. Tiến trình siết chặt bảo mật SSL từ Android 7 đến Android 15

```
+---------------------------------------------------------------------------------------+
| ANDROID 7 - 9 (API 24 - 28)                                                           |
| Chặn User Certificates mặc định. Phân tách System Store (/system/etc/security/cacerts)|
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
| ANDROID 10 - 13 (API 29 - 33)                                                         |
| Bật System-as-Root (SAR). Phân vùng /system chuyển sang Read-Only vĩnh viễn.          |
+---------------------------------------------------------------------------------------+
                                           │
                                           ▼
+---------------------------------------------------------------------------------------+
| ANDROID 14 - 15 (API 34+)                                                             |
| Di chuyển kho chứng chỉ hệ thống sang Conscrypt Mainline APEX module tại             |
| /apex/com.android.conscrypt/cacerts/ với cơ chế Mount Namespace riêng biệt.           |
+---------------------------------------------------------------------------------------+
```

---

## 6.2. Phân tích thư viện `android-certificate-trust` (AAR)

Kho mã nguồn `H:\reqble-mcp\android-certificate-trust` được nhóm phát triển Reqable phát hành nhằm giải quyết triệt để vấn đề bắt gói trên **máy Android chưa Root (Non-root)** cho các lập trình viên:

### Cách tích hợp vào dự án Android Studio:
Trong file `build.gradle` (hoặc `build.gradle.kts`):

```groovy
dependencies {
    // Chỉ kích hoạt trong môi trường build Debug
    debugImplementation("com.reqable.android:user-certificate-trust:1.0.0")
}
```

### Cơ chế hoạt động ngầm:
1. Khi biên dịch phiên bản Debug, trình hợp nhất manifest của Android (Manifest Merger) tự động nạp thẻ `networkSecurityConfig` từ thư viện:
   ```xml
   <application android:networkSecurityConfig="@xml/network_security_config"/>
   ```
2. Nội dung file `res/xml/network_security_config.xml`:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <network-security-config>
       <base-config cleartextTrafficPermitted="true">
           <trust-anchors>
               <certificates src="system" />
               <certificates src="user" />
           </trust-anchors>
       </base-config>
   </network-security-config>
   ```
3. Cấu hình này ép ứng dụng tin cậy cả chứng chỉ trong **User Store** (`<certificates src="user" />`), giúp giải mã toàn bộ HTTPS khi cài chứng chỉ Reqable mà không cần can thiệp quyền root.  
*Lưu ý:* Cơ chế này chỉ áp dụng cho ứng dụng native Android (Java/Kotlin dùng OkHttp, Retrofit, Webview). Nó không có tác dụng với Flutter hoặc React Native Hermes engine.

---

## 6.3. Cài đặt System Root CA (OpenSSL Hash, ADB 1-Click & Magisk Module)

Để giải mã toàn bộ ứng dụng trên thiết bị Android, chứng chỉ của Reqable bắt buộc phải được đưa vào kho lưu trữ hệ thống.

### Bước 1: Tính toán tên file theo chuẩn OpenSSL Subject Hash
Android định danh chứng chỉ hệ thống bằng giá trị băm cũ (Subject Hash Old):
```bash
# Trích xuất subject hash
HASH=$(openssl x509 -inform PEM -subject_hash_old -in reqable_ca.crt | head -1)

# Đổi tên file thành <hash>.0
cp reqable_ca.crt ${HASH}.0

# Nối thông tin text của chứng chỉ vào đuôi file
openssl x509 -inform PEM -text -in reqable_ca.crt -noout >> ${HASH}.0
```

### Bước 2: Cài đặt thủ công qua ADB (Cho máy Android 7 - 9 Rooted)
```bash
adb root
adb remount
adb push <hash>.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/<hash>.0
adb reboot
```

### Bước 3: Cài đặt qua Magisk Module (Hỗ trợ Android 10 đến 13)
Reqable có sẵn tính năng tự động đóng gói chứng chỉ CA thành module Magisk:
1. Trên giao diện Reqable Desktop: Bấm vào biểu tượng Khiên Certificate $\to$ Android $\to$ Chọn **Magisk Module** $\to$ Xuất file `reqable-cert-magisk.zip`.
2. Chuyển file zip vào điện thoại, mở Magisk App $\to$ Modules $\to$ *Install from storage* $\to$ Khởi động lại máy.
3. Module Magisk sử dụng cơ chế `mount -t tmpfs` để chèn file chứng chỉ vào phân vùng hệ thống trong quá trình boot mà không phá vỡ tính toàn vẹn `dm-verity`.

### Bước 4: Đột phá kỹ thuật trên Android 14 và Android 15 (Conscrypt APEX)
Trên Android 14+, chứng chỉ nằm tại `/apex/com.android.conscrypt/cacerts/`. Bản cập nhật Reqable v3.1+ đã nâng cấp script Magisk module để tự động bind mount vào mount namespace của Zygote:
```bash
# Lệnh thực thi trong module Magisk của Reqable trên Android 14+
mount --bind /data/local/tmp/cacerts /apex/com.android.conscrypt/cacerts
```
Đồng thời, tính năng **1-Click ADB Install** trong Reqable Desktop sẽ tự động phát hiện phiên bản Android 14/15 để áp dụng lệnh nạp tương ứng.

---

## 6.4. Các sắc thái đặc thù của Chrome và Mozilla Firefox trên Android

- **Google Chrome:** Đôi khi chủ động từ chối chứng chỉ tự ký nếu được cài vào System Store mà thiếu thuộc tính mở rộng. Giải pháp khuyến nghị: Thử cài vào **User Certificate Directory** trước; nếu không được mới cài vào System Directory.
- **Mozilla Firefox:** Firefox sử dụng kho lưu trữ chứng chỉ nội bộ riêng (NSS Store), hoàn toàn phớt lờ chứng chỉ của Android OS.  
  *Quy trình kích hoạt tin cậy:*
  1. Mở Firefox $\to$ Settings $\to$ About Firefox.
  2. Bấm liên tục 5 lần vào logo Firefox để mở **Secret Settings**.
  3. Quay lại Settings $\to$ Secret Settings $\to$ Bật tùy chọn **Use third party CA certificates**.

---

## 6.5. Chiến lược bypass SSL Pinning toàn diện (Java, Frida, LSPosed, Recompilation)

### Phương pháp 1: Frida Dynamic Instrumentation
Chích mã JavaScript vào bộ nhớ tiến trình để vô hiệu hóa kiểm tra chứng chỉ:

#### A. Hook lớp Java (OkHttp3 & X509TrustManager)
```javascript
Java.perform(function () {
    console.log("[*] Đang kích hoạt Frida SSL Unpinning...");

    // 1. Hook X509TrustManager chuẩn của Java
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');

    var CustomTrustManager = Java.registerClass({
        name: 'com.reqable.custom.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function (chain, authType) {},
            checkServerTrusted: function (chain, authType) {},
            getAcceptedIssuers: function () { return []; }
        }
    });

    var TrustManagers = [CustomTrustManager.$new()];
    var SSLContext_init = SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'Ljava.security.SecureRandom;'
    );
    SSLContext_init.implementation = function (keyManager, trustManager, secureRandom) {
        console.log("[+] Hooked SSLContext.init -> Chấp nhận mọi CA");
        SSLContext_init.call(this, keyManager, TrustManagers, secureRandom);
    };

    // 2. Hook OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (str, list) {
            console.log("[+] Hooked OkHttp3 CertificatePinner cho domain: " + str);
            return;
        };
    } catch (e) {
        console.log("[-] Không tìm thấy OkHttp3: " + e);
    }
});
```

#### B. Hook Native SSL Pinning trong Flutter (`libflutter.so`)
Dart runtime của Flutter tích hợp BoringSSL tĩnh bên trong `libflutter.so`. Đoạn script sau quét mẫu nhị phân ARM64 để patch hàm verify:

```javascript
function hookFlutter() {
    var m = Process.findModuleByName("libflutter.so");
    if (!m) {
        setTimeout(hookFlutter, 500);
        return;
    }
    console.log("[+] Tìm thấy libflutter.so tại base: " + m.base);

    // Mẫu nhị phân ARM64 cho hàm xác thực SSL của BoringSSL trong Flutter
    var pattern = "FF 83 01 D1 F6 57 03 A9 F4 4F 04 A9 FD 7B 05 A9 FD C3 01 91";
    Memory.scan(m.base, m.size, pattern, {
        onMatch: function (address, size) {
            console.log("[+] Tìm thấy hàm xác thực SSL của Flutter tại: " + address);
            Interceptor.attach(address, {
                onLeave: function (retval) {
                    console.log("[+] Ép giá trị trả về của Flutter cert verify thành OK (1)");
                    retval.replace(ptr(1));
                }
            });
        },
        onError: function (reason) {
            console.log("[-] Lỗi scan bộ nhớ: " + reason);
        },
        onComplete: function () {
            console.log("[*] Quét bộ nhớ hoàn tất.");
        }
    });
}
setTimeout(hookFlutter, 1000);
```

### Phương pháp 2: Sử dụng Module Xposed / LSPosed
Đối với môi trường kiểm thử ổn định lâu dài không cần cắm cáp chạy Frida:
- Cài đặt **LSPosed Framework** trên thiết bị có Magisk/KernelSU.
- Cài đặt các module mã nguồn mở hàng đầu:
  1. `JustTrustMe`: Hook toàn bộ các hàm mạng Java chuẩn (Apache, OkHttp, Retrofit, WebView).
  2. `TrustMeAlready`: Tương thích cao với Android 7 đến Android 13.

### Phương pháp 3: Recompilation & Patching Network Security Config
Áp dụng cho ứng dụng có tính năng phát hiện Root (Anti-Root / Play Integrity):
1. Dịch ngược file APK bằng Apktool: `apktool d target.apk -o unpacked/`
2. Mở file `unpacked/res/xml/network_security_config.xml`, xóa toàn bộ thẻ `<pin-set>`, thêm `<certificates src="user" />`.
3. Đóng gói lại và ký số APK bằng Uber-APK-Signer:
   ```bash
   apktool b unpacked/ -o patched.apk
   uber-apk-signer -a patched.apk
   ```

---

# 7. REPORT SERVER & TỰ ĐỘNG HÓA DAST

Tính năng **Report Server** (giới thiệu từ Reqable v2.20.0+) cho phép biến Reqable thành một nút thu thập và đẩy dữ liệu mạng tự động (Telemetry & DAST Node).

## 7.1. Kiến trúc Report Server và giao thức xuất dữ liệu HAR

Mỗi khi một phiên HTTP hoàn tất (cả chiều Request và Response), nếu URL khớp với quy tắc cấu hình, Reqable sẽ đóng gói phiên đó thành định dạng chuẩn quốc tế **HAR (HTTP Archive JSON)** và gửi một bản tin **HTTP POST** tới endpoint của Report Server.

```
[Reqable Core] ── Capture HTTP Session ──> [URL Pattern Match?]
                                                    │
                                             (Yes: Package HAR)
                                                    │
                                           [Compress: Gzip/Brotli/zstd]
                                                    │
                                        HTTP POST Stream (No Retry)
                                                    │
                                                    ▼
                                    [Report Server (FastAPI / DAST)]
```

### Headers đặc trưng đi kèm trong bản tin Report:
- `x-reqable-platform`: Hệ điều hành của thiết bị phát sinh dữ liệu (`windows`, `macos`, `linux`, `android`, `ios`).
- `x-reqable-reporter-host`: Hostname của phiên làm việc (ví dụ `api.github.com`).
- `x-reqable-reporter-rule`: Tên quy tắc cấu hình khớp trong Reqable.
- `Content-Encoding`: Thuật toán nén stream (`gzip`, `br`, `zstd`).

---

## 7.2. Phân tích mã nguồn triển khai FastAPI (`report-server-example`)

Repository `H:\reqble-mcp\report-server-example` cung cấp mã nguồn máy chủ tiếp nhận mẫu viết bằng Python FastAPI:

```python
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
import uvicorn
import gzip
from typing import Callable

# Lớp Request tùy biến tự động giải nén Gzip Body
class GzipRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            self._body = body
        return self._body

# Lớp Route can thiệp vào router của FastAPI
class GzipRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler

app = FastAPI()
app.router.route_class = GzipRoute

@app.post("/")
async def receive_report(request: Request, body: dict):
    platform = request.headers.get("x-reqable-platform")
    target_host = request.headers.get("x-reqable-reporter-host")
    print(f"[Report Server] Tiếp nhận báo cáo từ: {platform} | Host: {target_host}")
    
    # Bóc tách danh sách entries trong file HAR
    entries = body.get("log", {}).get("entries", [])
    for entry in entries:
        req = entry.get("request", {})
        res = entry.get("response", {})
        print(f" -> {req.get('method')} {req.get('url')} - Status: {res.get('status')}")
        
    return {"status": "success", "processed_entries": len(entries)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

---

## 7.3. Thiết lập hệ thống kiểm thử bảo mật tự động (DAST Pipeline)

Tận dụng Report Server để xây dựng quy trình kiểm thử bảo mật tự động:
1. Đội ngũ QA hoặc kỹ sư Automation chạy test case trên thiết bị thật có nối proxy Reqable.
2. Reqable stream toàn bộ các gói tin phát sinh về Report Server.
3. Report Server tự động bóc tách URL, Query Parameters, Headers và Form-data, sau đó tự động kích hoạt các công cụ quét lỗ hổng (Dynamic Application Security Testing - DAST):
   - Đẩy các URL có tham số vào **SQLMap API** để quét lỗ hổng SQL Injection.
   - Bắn các endpoint vào **Nuclei** hoặc **OWASP ZAP** để kiểm tra các lỗ hổng lộ lọt thông tin hoặc sai cấu hình CORS.
   - Gửi cảnh báo thời gian thực về Telegram/Slack nếu phát hiện mã lỗi HTTP 500 hoặc rò rỉ API key trong response.

---

# 8. 5 CASE STUDY THỰC CHIẾN REVERSE ENGINEERING

Dưới đây là 5 kịch bản thực chiến điển hình được tổng hợp chi tiết nhằm hướng dẫn giải quyết các bài toán khó khăn nhất khi phân tích ứng dụng.

## 8.1. Case Study 1: Bắt trọn vẹn Traffic ứng dụng Flutter (Mobile TUN VPN + Root CA)

### Bối cảnh & Thách thức:
- Ứng dụng di động viết bằng Flutter (Dart SDK) **hoàn toàn không sử dụng cấu hình Proxy của hệ thống Wi-Fi**. Dữ liệu mạng đi thẳng qua raw TCP socket ra Internet.
- Đồng thời, mã C++ của Dart Runtime (`Security_Context_linux.cc`) hardcode đường dẫn nạp CA tại `/system/etc/security/cacerts`, bỏ qua User Store của Android.

### Quy trình giải quyết từng bước:
1. **Bước 1 — Thu giữ gói tin tầng IP bằng TUN VPN (Collaborative Mode):**
   - Khởi động Reqable Desktop trên máy tính. Nhấp vào biểu tượng Điện thoại trên thanh toolbar để mở mã QR kết nối.
   - Cài đặt ứng dụng **Reqable Mobile** trên điện thoại Android/iOS (cùng kết nối chung mạng Wi-Fi với PC).
   - Mở Reqable Mobile, chọn chế độ **Collaborative Mode**, quét mã QR trên màn hình PC.
   - Bật tính năng **Enhanced Mode** trên Reqable Mobile. Hệ điều hành Android sẽ xin cấp quyền tạo kết nối VPN ảo (TUN Interface). Tất cả các gói tin IP (Layer 3) phát ra từ ứng dụng Flutter sẽ bị TUN interface hứng trọn và chuyển tiếp về Reqable Desktop.
2. **Bước 2 — Giải mã HTTPS SSL:**
   - Đối với máy Android đã Root: Mở Reqable Desktop, vào `Certificate -> Install Certificate on Mobile Device -> Android`, chọn cài đặt tự động qua ADB hoặc cài đặt module Magisk. Chứng chỉ CA của Reqable sẽ nằm trong `/system/etc/security/cacerts/`.
3. **Bước 3 — Vượt qua SSL Pinning của Flutter (nếu có):**
   - Khởi chạy script Frida quét pattern bộ nhớ `libflutter.so` (như đã hướng dẫn ở Mục 6.5) để vô hiệu hóa hàm `ssl_crypto_x509_session_verify_cert_chain`.
   - Kết quả: Toàn bộ các gói tin API của Flutter hiển thị đầy đủ nội dung JSON rõ ràng trên Reqable Desktop.

---

## 8.2. Case Study 2: Ép ứng dụng Desktop né proxy đi qua Reqable với Proxifier

### Bối cảnh:
Nhiều ứng dụng trên máy tính (Windows/macOS) như game launcher, ứng dụng Flutter Desktop, tool CLI, hoặc phần mềm độc hại (malware) cố tình bỏ qua cài đặt System Proxy của Windows.

### Quy trình thiết lập Proxifier phối hợp Reqable:
1. **Thiết lập Proxy Server trong Proxifier:**
   - Mở Proxifier $\to$ `Profile` $\to$ `Proxy Servers` $\to$ `Add`.
   - Điền Address: `127.0.0.1`, Port: `9000` (cổng lắng nghe của Reqable).
   - Protocol: Chọn **HTTPS** (hoặc SOCKS5).
2. **Cấu hình Quy tắc Chống Vòng Lặp Vô Tận (Loopback Avoidance - BẮT BUỘC):**
   - Bản thân Reqable.exe cần gửi request ra ngoài Internet. Nếu Proxifier lại bắt request outbound của Reqable rồi nạp ngược lại vào cổng 9000, sẽ tạo ra vòng lặp vô tận (Infinite Loop) làm crash mạng.
   - Vào `Profile` $\to$ `Proxification Rules` $\to$ `Add`:
     - Tên rule: `Reqable Direct`
     - Applications: Nhập `Reqable.exe`
     - Action: Chọn **Direct**.
3. **Cấu hình Quy tắc Bắt Ứng Dụng Đích:**
   - Tạo rule mới trong Proxification Rules:
     - Applications: Nhập tên file thực thi cần bắt (ví dụ `TargetApp.exe; flutter_test.exe`).
     - Action: Chọn Proxy vừa tạo (`127.0.0.1:9000`).
   - Quy tắc `Default` đặt thành **Direct**.
4. **Kết quả:** Không cần bật System Proxy trong Reqable, toàn bộ lưu lượng của `TargetApp.exe` bị ép đi qua Reqable và hiển thị chi tiết.

---

## 8.3. Case Study 3: Dịch ngược API mã hóa đối xứng AES & ký số MD5 động

### Bối cảnh:
Một ứng dụng mua sắm trực tuyến thực hiện hai lớp bảo vệ:
1. Toàn bộ response body trả về bị mã hóa bằng thuật toán AES-128-CBC.
2. Khi gửi request, ứng dụng yêu cầu header `x-signature` tính bằng mã băm MD5 của chuỗi query cộng với chuỗi bí mật (Salt) để chống can thiệp tham số.

### Kịch bản giải quyết bằng Python Scripting:
1. Mở menu `Traffic -> Script` (`Shift + Ctrl + P`), thêm một quy tắc mới áp dụng cho domain `api.myshop.com/*`.
2. Soạn thảo mã Python kết hợp cả hai chiều xử lý:

```python
from reqable import *
import hashlib
import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

KEY = b'SecretKeyShop123'
IV  = b'SecretIVShop1234'
SALT = "MyShopSaltKey2026"

def decrypt_aes(ciphertext: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(decrypted_data) + unpadder.finalize()

def onRequest(context, request):
    # Chiều đi: Tự động tính toán lại chữ ký MD5 nếu kỹ sư sửa đổi query
    sorted_queries = sorted(request.queries)
    raw_query_string = HttpQueries(sorted_queries).concat()
    
    hasher = hashlib.md5()
    hasher.update((raw_query_string + SALT).encode('utf-8'))
    new_signature = hasher.hexdigest()
    
    request.headers['x-signature'] = new_signature
    context.comment = f"Re-signed: {new_signature[:8]}..."
    return request

def onResponse(context, response):
    # Chiều về: Tự động giải mã ciphertext hiển thị JSON rõ ràng
    if response.body.isText:
        try:
            cipher_bytes = base64.b64decode(response.body.payload)
            plain_text = decrypt_aes(cipher_bytes).decode('utf-8')
            response.body.text(plain_text)
            response.headers['Content-Type'] = 'application/json'
            context.highlight = Highlight.green
        except Exception as e:
            context.highlight = Highlight.red
            print(f"Decryption error: {e}")
    return response
```
3. **Hiệu quả:** Kỹ sư có thể thoải mái dùng tính năng Compose hoặc Breakpoint để thay đổi giá sản phẩm trên giao diện, Reqable sẽ tự động tính lại chữ ký hợp lệ để vượt qua kiểm tra của máy chủ, và giải mã phản hồi để hiển thị ngay lập tức.

---

## 8.4. Case Study 4: Debug CLI Scripts & Automation Tools bằng Proxy Terminal 1-Click

### Bối cảnh:
Khi viết các script tự động hóa cào dữ liệu (crawler) hoặc bot kiểm thử bằng Python (`requests`), Node.js (`axios`) hoặc `curl`, việc thiết lập proxy thường xuyên vấp phải lỗi kinh điển:
`SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] self signed certificate in certificate chain`

### Quy trình giải quyết:
1. Mở menu `Tools -> Proxy Terminal` (hoặc phím tắt `Alt + T`).
2. Reqable mở một cửa sổ console chuyên dụng (PowerShell hoặc Bash). Trong cửa sổ này, Reqable đã tự động export các biến môi trường:
   ```bash
   HTTP_PROXY=http://127.0.0.1:9000
   HTTPS_PROXY=http://127.0.0.1:9000
   ALL_PROXY=http://127.0.0.1:9000
   SSL_CERT_FILE=C:\Users\...\AppData\Roaming\Reqable\reqable_ca.crt
   REQUESTS_CA_BUNDLE=C:\Users\...\AppData\Roaming\Reqable\reqable_ca.crt
   NODE_EXTRA_CA_CERTS=C:\Users\...\AppData\Roaming\Reqable\reqable_ca.crt
   ```
3. Chạy trực tiếp các câu lệnh:
   ```bash
   python my_crawler.py
   # hoặc
   npm test
   # hoặc
   curl -I https://api.github.com
   ```
4. Toàn bộ các kết nối từ script tự động đi qua Reqable và tự động tin cậy chứng chỉ MITM mà **không cần chỉnh sửa bất kỳ dòng code nào trong dự án**.

---

## 8.5. Case Study 5: Mock dữ liệu lỗi & Chaos Engineering cho Mobile App

### Bối cảnh:
Kiểm thử khả năng phục hồi của ứng dụng di động khi máy chủ gặp sự cố: Ứng dụng có bị crash không nếu API trả về mã lỗi 503 Service Unavailable, hoặc ứng dụng xử lý thế nào khi người dùng đi vào vùng sóng yếu (hầm gửi xe, thang máy)?

### Quy trình thiết lập trong Reqable:
1. **Bước 1 — Giả lập lỗi máy chủ bằng Rewrite:**
   - Vào `Traffic -> Rewrite` (`Shift + Ctrl + K`), thêm quy tắc mới.
   - URL: `https://api.myapp.com/v2/user/profile`
   - Chọn chế độ: **Replace Response**
   - Đặt Status Code: `503`
   - Nhập nội dung Body:
     ```json
     {
       "error": "DatabaseMaintenance",
       "message": "Hệ thống đang bảo trì định kỳ, vui lòng thử lại sau 15 phút.",
       "code": 50301
     }
     ```
   - Kiểm tra trên app: Xác nhận ứng dụng hiển thị thông báo lỗi thân thiện thay vì bị sập (crash).
2. **Bước 2 — Giả lập điều kiện mạng chập chờn bằng Network Throttling:**
   - Mở `Traffic -> Network Throttling` (`Alt + J`).
   - Chọn profile **Bad Network**:
     - Băng thông Download: 64 Kbps
     - Độ trễ Latency: 2500 ms
     - Tỉ lệ rớt gói Packet Loss: 20%
   - Thử nghiệm thao tác thanh toán trên app di động: Đánh giá xem ứng dụng có hiển thị biểu tượng loading đúng cách, có xử lý cơ chế retry an toàn không gây trừ tiền hai lần hay không.

---

# TỔNG KẾT

Reqable đã định nghĩa lại tiêu chuẩn của một phần mềm kiểm thử API và bắt gói tin mạng thế hệ mới. Với kiến trúc C++ Native siêu tốc, giao diện Flutter hiện đại, khả năng mở rộng không giới hạn qua Python Scripting, tích hợp AI Agent qua giao thức MCP, và các giải pháp can thiệp chuyên sâu trên Android/iOS, Reqable là vũ khí không thể thiếu trong kho công cụ của mọi lập trình viên, kỹ sư QA, chuyên gia kiểm thử xâm nhập (Pentester) và nhà phân tích dịch ngược phần mềm.
