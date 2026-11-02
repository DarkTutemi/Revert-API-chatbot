---
name: binary-api-reverse-engineer
description: >-
  Dịch ngược (reverse engineer) API endpoint, giao thức mạng và mô hình dữ liệu từ file nhị phân Android APK và
  Windows EXE. Sử dụng khi cần decompile ứng dụng di động hoặc phần mềm máy tính, bypass SSL pinning (Frida / Magisk / APEX),
  bắt traffic REST, gRPC, Protobuf hoặc WebSocket qua proxy Reqable, phân tích giao thức nhị phân không có file schema .proto,
  hoặc tái cấu trúc sinh SDK client typed bằng Python/TypeScript từ file thực thi.
---

# Kỹ Năng Dịch Ngược API Từ File Nhị Phân & Di Động (APK & EXE)

Kỹ năng này cung cấp một phương pháp luận từ đầu đến cuối và chuỗi công cụ tự động hóa sẵn dùng để trích xuất hợp đồng API, giải mã lưu lượng mạng mã hóa, decode các giao thức nhị phân và tạo ra các SDK client có kiểu dữ liệu rõ ràng (typed) từ file APK Android và ứng dụng Windows desktop đã biên dịch.

---

## 1. Kiến Trúc Cấu Trúc liên Kết (Architectural Topology)

Các ứng dụng đã biên dịch thường đóng gói logic mạng bên trong bytecode (DEX, CIL) hoặc mã máy native (ARM64, x86_64) và thực thi các biện pháp ghim chứng chỉ (Certificate Pinning) nghiêm ngặt. Việc chặn bắt gói tin đòi hỏi phải định tuyến lưu lượng qua proxy MITM của Reqable đồng thời vô hiệu hóa các cơ chế kiểm tra chứng chỉ:

```
+-----------------------------------------------------------------------------------+
|                           TẦNG ỨNG DỤNG MỤC TIÊU                                  |
|                                                                                   |
|  [Android APK]                                    [File Thực Thi Windows (EXE)]  |
|   - Java / Kotlin (OkHttp / Retrofit)              - .NET Managed (HttpClient)    |
|   - Flutter (BoringSSL trong libflutter.so)        - Electron / CEF (Chromium)    |
|   - Native C/C++ (libcurl / BoringSSL)             - Native PE (WinHTTP, WinINet) |
+----------------------------------------+------------------------------------------+
                                         |
                       [TẦNG BYPASS & GỠ GHIM SSL (UNPINNING)]
                         - Android: Frida (`universal_ssl_unpin.js`)
                         - System CA: Magisk Module / Mount đè Conscrypt APEX
                         - Windows: Hook WinHTTP / Chuyển hướng Winsock qua Proxifier
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       ĐỊNH TUYẾN & TẠO ĐƯỜNG HẦM MẠNG                             |
|  - Android Tiêu Chuẩn: Wi-Fi Proxy (192.168.1.x:9000)                             |
|  - Android Không Nhận Proxy (Flutter/Go): Reqable Collaborative Mode (TUN / VPN)   |
|  - Windows Không Nhận Proxy: Proxifier (Tránh Vòng Lặp: Target -> 9000, Reqable -> Direct)|
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       ENGINE PROXY REQABLE MITM (:9000)                           |
|  - Giải mã TLS 1.2 / 1.3, HTTP/2, HTTP/3 QUIC, Luồng WebSocket và gRPC           |
|  - Can Thiệp Động Gói Tin: Quy Tắc Rewrite, Điểm Ngắt Breakpoint, Python Script   |
|  - Soi Giao Thức Thời Gian Thực: REST JSON, Cây Protobuf, Gán File Đặc Tả Proto   |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       TÁI CẤU TRÚC & TỰ ĐỘNG TẠO CLIENT SDK                       |
|  - `jadx_api_extractor.py`   -> Danh mục API & trích xuất Secret Token / Khóa API |
|  - `protobuf_decoder.py`     -> Giải mã wire-format & tạo file đặc tả `.proto`    |
|  - `api_client_generator.py` -> Bộ SDK typed Python (`httpx`+`pydantic`) & TS     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Chuẩn Bị & Kiểm Tra Bộ Công Cụ (Toolchain Prerequisites)

Kiểm tra sự sẵn sàng của các công cụ dịch ngược và can thiệp động (instrumentation) trên môi trường máy chủ:

| Công cụ | Lệnh Kiểm Tra CLI | Đường Dẫn Điển Hình | Mục Đích Sử Dụng |
|:---|:---|:---|:---|
| **jadx** | `jadx --version` | PATH (`jadx.bat` / `jadx`) | Decompile mã DEX sang Java & trích xuất tài nguyên |
| **Frida** | `frida --version` | PATH (`frida.exe`) | Can thiệp nhị phân động (DBI) & tiêm mã hook |
| **ADB** | `adb version` | Android SDK `platform-tools` | Giao tiếp thiết bị, mở shell và quản lý chứng chỉ CA |
| **Python** | `python --version` | Python 3.10+ | Chạy các script bổ trợ & mã nguồn client |
| **Reqable** | Listener cổng 9000 | `Reqable.exe` | Proxy MITM, bắt gói tin & phân tích giao thức |
| **Proxifier**| Kiểm tra GUI / Tiến trình | `Proxifier.exe` | Chuyển hướng mạng Winsock SPI cho các file EXE cứng đầu |
| **dnSpy / ILSpy**| Kiểm tra CLI / GUI | `ilspycmd` | Decompiler CIL cho các ứng dụng Windows .NET |

---

## 3. Quy Trình Dịch Ngược Tĩnh (Static Reverse Engineering)

Phân tích tĩnh giúp làm lộ các endpoint, URL gốc (base URL), khóa ký mật mã (signature key) và các model request/response trước khi ứng dụng chạy.

### 3.1 Phân Tích Tĩnh Android APK

#### A. Decompile Bằng `jadx`
```bash
# Decompile tốc độ cao không giải mã tài nguyên (phù hợp tìm kiếm mã nguồn nhanh)
jadx -d ./decompiled_code --no-res ./target.apk

# Decompile đầy đủ kèm chế độ deobfuscation (phục hồi tên biến/hàm bị R8/ProGuard làm rối)
jadx -d ./decompiled_app --deobf --deobf-min 3 ./target.apk
```

#### B. Trích Xuất API Tự Động Qua `jadx_api_extractor.py`
Sử dụng script tích hợp sẵn để phân tích cú pháp các interface Retrofit, OkHttp builder, base URL gán cứng và các bí mật (secret key) bị nhúng trong mã nguồn:

```bash
# Trích xuất trực tiếp từ file APK:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\jadx_api_extractor.py \
  -i ./target.apk \
  -o ./extracted_api.json

# Trích xuất từ một thư mục mã nguồn đã decompile trước đó:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\jadx_api_extractor.py \
  -i ./decompiled_app \
  -o ./extracted_api.json \
  -f json
```

Script sẽ xuất ra file JSON có cấu trúc rõ ràng:
```json
{
  "app_info": {
    "package": "com.example.service",
    "network_security_config": "@xml/network_security_config"
  },
  "base_urls": ["https://api.example.com"],
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/v2/auth/login",
      "base_url": "https://api.example.com",
      "full_url": "https://api.example.com/api/v2/auth/login",
      "headers": {"Content-Type": "application/json"},
      "query_params": [],
      "path_params": [],
      "body_type": "LoginRequest",
      "return_type": "Call<AuthResponse>",
      "source_file": "com/example/api/AuthApi.java",
      "source_line": 34
    }
  ],
  "extracted_keys": [
    {
      "key": "AIzaSyD-EXAMPLEKEY12345",
      "type": "Google API Key",
      "source": "resources/res/values/strings.xml"
    }
  ]
}
```

#### C. Nhận Diện Chữ Ký Request & Các Lớp Interceptor
1. Tìm kiếm `okhttp3.Interceptor` trong mã nguồn đã decompile:
   ```bash
   grep -rn "implements Interceptor" ./decompiled_app/sources/
   ```
2. Tìm kiếm thuật toán tạo chữ ký số (sign calculation):
   - `HmacSHA256`, `HmacSHA1`, `MessageDigest.getInstance("MD5")`
   - Công thức phổ biến: sắp xếp tham số theo alphabet rồi băm mật mã:
     $$\text{sign} = \text{HMAC-SHA256}(\text{url} + \text{timestamp} + \text{body}, \text{secret})$$

#### D. Vá Lại APK Bằng `apktool` (Giải pháp thay thế khi không dùng được Frida)
Nếu việc gắn hook động bị chặn bởi các lớp bảo vệ chống can thiệp (anti-tamper):
```bash
# 1. Bung gói APK
apktool d target.apk -o unpacked/

# 2. Tiêm file cấu hình bảo mật mạng cho phép cert người dùng
cp C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\resources\network_security_config.xml unpacked/res/xml/

# 3. Thêm thuộc tính android:networkSecurityConfig vào thẻ <application> trong file unpacked/AndroidManifest.xml:
#    <application android:networkSecurityConfig="@xml/network_security_config" ...>

# 4. Đóng gói lại và ký số
apktool b unpacked/ -o patched.apk
uber-apk-signer -a patched.apk
```

---

### 3.2 Phân Tích Tĩnh File Thực Thi Windows (EXE/DLL)

#### A. Phân Loại Nền Tảng Công Nghệ Của Ứng Dụng
Xác định stack công nghệ của ứng dụng trước khi tiến hành phân tích:
- **Ứng dụng Quản lý .NET (.NET Managed Binary):** Kiểm tra danh sách thư viện import có chứa `mscoree.dll`.
  - Công cụ: Mở binary bằng `dnSpy` hoặc chạy `ilspycmd -p -o ./decompiled_csharp Target.exe`.
  - Tìm kiếm các lớp `HttpClient`, `RestSharp` và các model DTO có annotation `[JsonProperty]`.
- **Ứng dụng Electron / CEF (Chromium Embedded Framework):**
  - Tìm file `resources/app.asar` trong thư mục cài đặt.
  - Giải nén gói:
    ```bash
    npx asar extract "C:\Program Files\TargetApp\resources\app.asar" ./unpacked_asar
    grep -rnE "https?://[a-zA-Z0-9\.\-_]+/api" ./unpacked_asar/
    ```
  - Khởi chạy trực tiếp kèm tham số proxy:
    ```bash
    "C:\Program Files\TargetApp\TargetApp.exe" --proxy-server="http://127.0.0.1:9000" --ignore-certificate-errors
    ```
- **File Nhị Phân Native PE (C/C++, Rust, Go):**
  - Trích xuất chuỗi: `strings -a Target.exe | grep -E "https?://"`
  - Kiểm tra DLL import qua `PE-bear` hoặc lệnh `dumpbin /imports Target.exe`:
    - `WINHTTP.dll`: `WinHttpOpen`, `WinHttpConnect`, `WinHttpSendRequest`
    - `WININET.dll`: `InternetOpenW`, `HttpSendRequestW`
    - `libcurl.dll`: `curl_easy_init`, `curl_easy_setopt`
  - Mở trong Ghidra / IDA Pro: Tìm các vị trí tham chiếu chéo (XREFs) đến các chuỗi URL endpoint đã phát hiện.

---

## 4. Bắt Traffic Động & Vượt Chặn Ghim Chứng Chỉ (SSL Unpinning)

### 4.1 Ma Trận Tin Cậy Chứng Chỉ Trên Android (Certificate Trust Matrix)

| Phiên Bản Android | Nơi Lưu Chứng Chỉ Hệ Thống | Quy Trình Cài Đặt Chứng Chỉ CA |
|:---|:---|:---|
| **Android 7 – 9** (API 24–28) | `/system/etc/security/cacerts/` | Remount phân vùng system thành RW hoặc copy cert qua ADB root: `adb push <hash>.0 /system/etc/security/cacerts/` |
| **Android 10 – 13** (API 29–33) | Phân vùng System-as-Root (SAR) Read-Only | Cài chứng chỉ Reqable CA qua **Magisk Module** (mount tmpfs đè lên `/system/etc/security/cacerts`) |
| **Android 14 – 15** (API 34+) | Phân vùng Module Conscrypt APEX | Thực hiện bind-mount chứng chỉ vào container APEX: `mount --bind /data/local/tmp/cacerts /apex/com.android.conscrypt/cacerts/` |

#### Tự Động Tính Hash Cho Chứng Chỉ Android
```bash
# Tính hash OpenSSL subject_hash_old (Android yêu cầu chuẩn này)
HASH=$(openssl x509 -inform PEM -subject_hash_old -in reqable_ca.crt | head -1)
cp reqable_ca.crt ${HASH}.0
openssl x509 -inform PEM -text -in reqable_ca.crt -noout >> ${HASH}.0
chmod 644 ${HASH}.0
```

---

### 4.2 Script Frida Đa Nền Tảng Gỡ Ghim SSL (`universal_ssl_unpin.js`)

File script `scripts/universal_ssl_unpin.js` tích hợp sẵn khả năng bypass toàn diện cho nhiều engine:
1. Java `X509TrustManager` & `SSLContext.init`
2. OkHttp3 / OkHttp4 `CertificatePinner` (Bao gồm cả các hàm bị obfuscate trên Kotlin)
3. Conscrypt & Google Play Services `TrustManagerImpl`
4. Android `NetworkSecurityConfigProvider` & `RootTrustManager`
5. Android WebView `WebViewClient.onReceivedSslError`
6. Quét mẫu bộ nhớ BoringSSL (ARM64 & ARMv7) trong `libflutter.so` của ứng dụng Flutter
7. Thư viện native trên Windows: WinHTTP (`winhttp.dll`), OpenSSL và libcurl

#### Các Lệnh Chạy Bằng Frida
```bash
# Android: Tự động khởi chạy ứng dụng (spawn) và nạp script unpin ngay lập tức
frida -U -f com.target.app -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js

# Android: Đính kèm (attach) vào tiến trình ứng dụng đang mở sẵn
frida -U -n com.target.app -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js

# Windows: Khởi chạy file thực thi desktop kèm script unpin
frida -f "C:\Program Files\TargetApp\Target.exe" -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js
```

---

### 4.3 Các Cơ Chế Định Tuyến Proxy Trên Android

1. **Proxy HTTP Cấu Hình Wi-Fi Chuẩn:**
   - Cài đặt trong mục Wi-Fi trên thiết bị Android: Proxy Host = `<IP_Máy_Tính>`, Proxy Port = `9000`.
2. **Lệnh Thiết Lập Global Proxy Qua ADB:**
   ```bash
   adb shell settings put global http_proxy 192.168.1.192:9000
   # Hủy thiết lập:
   adb shell settings put global http_proxy :0
   ```
3. **Chế Độ Phối Hợp Reqable (Collaborative Mode qua TUN / VPN Driver):**
   - Áp dụng cho các ứng dụng phớt lờ cấu hình proxy hệ thống (như Flutter, Dart, Go, React Native Hermes, Unreal Engine):
   - Mở ứng dụng Reqable Mobile trên thiết bị Android.
   - Kết nối vào chế độ **Collaborative Mode**, ghép đôi với phần mềm Reqable Desktop qua cổng 9000.
   - Toàn bộ gói tin IP ở tầng network adapter ảo sẽ được bắt trọn và chuyển tiếp qua Wi-Fi nội bộ về Reqable Desktop.

---

### 4.4 Bắt Gói Tin Ứng Dụng Windows Desktop (Bằng Proxifier)

Đối với các ứng dụng Windows không nhận cài đặt proxy của hệ thống Windows:

#### Cấu Hình Bắt Buộc Để Tránh Vòng Lặp Mạng (Loopback Avoidance)
1. Mở Proxifier -> **Profile** -> **Proxy Servers**:
   - Thêm proxy `127.0.0.1:9000` (Giao thức: HTTPS hoặc SOCKS5).
2. Thiết lập mục **Proxification Rules**:
   - **Rule 1 (Bỏ Qua Reqable - BẮT BUỘC):**
     - Applications: `Reqable.exe`
     - Action: **Direct** (Đi thẳng, không qua proxy)
   - **Rule 2 (Bắt Gói Ứng Dụng Mục Tiêu):**
     - Applications: `TargetApp.exe; electron.exe; curl.exe`
     - Action: **Proxy 127.0.0.1:9000**
   - **Rule 3 (Default):**
     - Action: **Direct**

---

## 5. Phân Tích Giao Thức: REST, Protobuf, gRPC & WebSocket

### 5.1 Giải Mã Wire-Format Giao Thức Protobuf (`protobuf_decoder.py`)

Khi dịch ngược ứng dụng di động hoặc binary, các request thường mang dữ liệu Protocol Buffers thô mà không có sẵn file định nghĩa schema `.proto`.

Sử dụng `scripts/protobuf_decoder.py` để phân tích đệ quy cấu trúc wire-format (varint, 64-bit, length-delimited submessage, 32-bit float) và tự động dựng lại schema `.proto` chuẩn:

```bash
# Giải mã trực tiếp từ chuỗi Hex:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\protobuf_decoder.py \
  -i "0a0474657374109601" \
  --hex \
  --export-proto ./reconstructed.proto

# Giải mã từ file binary payload thô xuất ra từ Reqable:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\protobuf_decoder.py \
  -i ./payload.bin \
  -o ./decoded_payload.json \
  --export-proto ./schema.proto
```

#### Ví Dụ Schema Được Tái Dựng Tự Động
```protobuf
syntax = "proto3";

package reconstructed;

message ReconstructedMessage {
    string field_1 = 1;
    int64 field_2 = 2;
    SubMessage_3 field_3 = 3;
}

message SubMessage_3 {
    double field_1 = 1;
    bytes field_2 = 2;
}
```

### 5.2 Cơ Chế gRPC Reflection & Gán File Proto Vào Reqable
1. **gRPC Reflection:** Nếu máy chủ hỗ trợ `grpc.reflection.v1alpha.ServerReflection`, Reqable sẽ tự động khám phá danh sách service và hiển thị cây dữ liệu dạng JSON dễ đọc.
2. **Gán File Proto Thủ Công:** Nếu reflection bị tắt, lưu file `.proto` đã được tái dựng bởi `protobuf_decoder.py` và nạp vào Reqable Desktop tại mục `Settings -> Proto -> Add Spec File`.

### 5.3 Soi Luồng Dữ Liệu WebSocket
Reqable bắt đầy đủ các khung (frame) của WebSocket (`Opcode 0x1` Text, `Opcode 0x2` Binary):
- Khung văn bản (Socket.IO, STOMP): Xem trực tiếp JSON đã định dạng trong tab WebSocket Message.
- Khung nhị phân (Binary): Xuất dữ liệu payload thành file `.bin` rồi chuyển tiếp vào `protobuf_decoder.py` để giải mã.

---

## 6. Quy Trình Tái Cấu Trúc Mã Nguồn Client (`api_client_generator.py`)

Chuyển đổi danh mục các endpoint đã trích xuất thành bộ SDK hoàn chỉnh sẵn sàng sử dụng:

```bash
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\api_client_generator.py \
  -i ./extracted_api.json \
  -o ./generated_sdk \
  --client-name "ServiceApiClient" \
  --language both
```

### 6.1 Ví Dụ Mã Client Python Được Sinh Ra (`httpx` + `pydantic`)
```python
import asyncio
from client import ServiceApiClient

async def main():
    async with ServiceApiClient(auth_token="SESSION_TOKEN") as client:
        # Hàm được định kiểu chặt chẽ với path params và query params
        profile = await client.get_users_profile(id="user_123", details=True)
        print("Dữ liệu profile:", profile)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Ví Dụ Mã Client TypeScript Được Sinh Ra (`fetch`)
```typescript
import { ServiceApiClient } from "./client";

async function run() {
    const client = new ServiceApiClient({
        authToken: "SESSION_TOKEN"
    });

    const profile = await client.getUsersProfile("user_123", { details: true });
    console.log("Dữ liệu profile:", profile);
}

run();
```

---

## 7. Bảng Xử Lý Sự Cố (Troubleshooting Matrix)

| Vấn đề | Nguyên nhân gốc rễ | Giải pháp |
|:---|:---|:---|
| **Ứng dụng crash ngay khi Frida vừa spawn** | Có cơ chế phát hiện Anti-Frida (quét cổng 27042 của `frida-server`, soi `/proc/self/maps` hoặc tên thread) | Chạy Frida ở chế độ ẩn danh (`frida-server -l 127.0.0.1:44821`), sử dụng Magisk Zygisk-Shamiko hoặc bản Hluda (bản Frida đã đổi tên các chuỗi nhận diện). |
| **Lỗi SSL Handshake trên Android 14/15** | Chứng chỉ cài trong `/system/etc/security/cacerts` bị bỏ qua bởi Conscrypt APEX | Thực hiện lệnh bind-mount APEX bên trong namespace của Zygote: `mount --bind /data/local/tmp/cacerts /apex/com.android.conscrypt/cacerts`. |
| **Kết nối HTTPS của Flutter không đi qua Reqable** | BoringSSL của Dart bỏ qua proxy hệ điều hành và chứng chỉ user | Dùng chế độ Collaborative Mode của Reqable (bắt gói qua TUN VPN) + tiêm `universal_ssl_unpin.js` để quét mẫu bộ nhớ `libflutter.so`. |
| **Mạng bị lặp vô tận / Crash trên Windows** | Proxifier chặn và chuyển hướng ngược lại lưu lượng của chính Reqable | Thêm quy tắc trong Proxifier: `Application: Reqable.exe -> Action: Direct` (phải đặt quy tắc này nằm trên quy tắc của ứng dụng cần proxy). |
| **Trường Protobuf hiển thị chuỗi hex thô** | Dữ liệu bên trong đã bị mã hóa hoặc nén trước khi đóng gói protobuf | Kiểm tra xem byte đầu có phải `1f 8b` (Gzip) hoặc `78 9c` (Zlib) hay không; giải nén trước khi phân tích bằng `protobuf_decoder.py`. |
| **Không tìm thấy endpoint Retrofit khi quét tĩnh** | Mã nguồn bị làm rối bằng R8 / DexGuard và các chuỗi đã bị mã hóa | Dùng `jadx --deobf` hoặc trích xuất chuỗi động trong bộ nhớ bằng lệnh `Memory.scan` của Frida. |

---

## 8. Tóm Tắt Các Script Hỗ Trợ Trong Thư Mục `scripts/`

| Tên Script | Ngôn Ngữ | Mô Tả & Khả Năng Chính |
|:---|:---|:---|
| `universal_ssl_unpin.js` | JavaScript (Frida) | Script gỡ ghim SSL đa nền tảng cho Java TrustManager, OkHttp3/4, Conscrypt, WebView, Flutter BoringSSL ARM64/v7 và Windows WinHTTP. |
| `jadx_api_extractor.py` | Python 3 | Decompile file APK qua jadx, phân tích annotation của Retrofit, base URL, tài nguyên XML và các khóa bí mật thành JSON có cấu trúc. |
| `protobuf_decoder.py` | Python 3 | Bộ giải mã wire-format thuần Python, đệ quy bóc tách gói nhị phân Protobuf khi không có schema và tự động xuất ra file `.proto`. |
| `api_client_generator.py` | Python 3 | Chuyển đổi danh mục API JSON thành bộ SDK client typed bất đồng bộ bằng Python (`httpx` + `pydantic`) và TypeScript. |
