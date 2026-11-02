---
name: binary-api-reverse-engineer
description: >-
  Reverse engineer API endpoints, protocols, and data models from Android APK and
  Windows EXE binaries. Use when the user asks to decompile mobile apps or desktop
  software, bypass SSL pinning (Frida / Magisk / APEX), intercept REST, gRPC, Protobuf,
  or WebSocket traffic via Reqable proxy, analyze binary protocols without .proto schemas,
  or reconstruct typed Python/TypeScript API client SDKs from binaries.
---

# Mobile and Binary API Reverse Engineering (APK & EXE)

This skill provides an end-to-end methodology and ready-to-run automation toolchain for extracting API contracts, decrypting encrypted traffic, decoding binary protocols, and generating typed API client SDKs from compiled Android APKs and Windows desktop applications.

---

## 1. Architectural Topology

Compiled applications encapsulate network logic within bytecode (DEX, CIL) or native machine code (ARM64, x86_64) and enforce strict certificate pinning. Interception requires routing traffic through Reqable's MITM proxy while neutralizing trust verification checks:

```
+-----------------------------------------------------------------------------------+
|                            TARGET APPLICATION LAYER                               |
|                                                                                   |
|  [Android APK]                                    [Windows Binary (EXE)]         |
|   - Java / Kotlin (OkHttp / Retrofit)              - .NET Managed (HttpClient)    |
|   - Flutter (BoringSSL in libflutter.so)           - Electron / CEF (Chromium)    |
|   - Native C/C++ (libcurl / BoringSSL)             - Native PE (WinHTTP, WinINet) |
+----------------------------------------+------------------------------------------+
                                         |
                       [SSL UNPINNING & BYPASS LAYER]
                         - Android: Frida (`universal_ssl_unpin.js`)
                         - System CA: Magisk Module / Conscrypt APEX bind-mount
                         - Windows: WinHTTP hook / Proxifier Winsock redirect
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        NETWORK ROUTING & TUNNELING                                |
|  - Android Standard: Wi-Fi Proxy (192.168.1.x:9000)                               |
|  - Android Unaware (Flutter/Go): Reqable Collaborative Mode (TUN / VPN Driver)    |
|  - Windows Proxy-Unaware: Proxifier (Loopback-Safe: Target -> 9000, Reqable -> Direct)|
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       REQABLE MITM PROXY ENGINE (:9000)                           |
|  - Decrypts TLS 1.2 / 1.3, HTTP/2, HTTP/3 QUIC, WebSocket, and gRPC Streams       |
|  - Dynamic Packet Tampering: Rewrite Rules, Breakpoint Executor, Python Scripting |
|  - Live Protocol Inspection: REST JSON, Protobuf Trees, Spec File Association    |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                      RECONSTRUCTION & CLIENT GENERATION                           |
|  - `jadx_api_extractor.py`   -> Structured API catalog & secret token extraction  |
|  - `protobuf_decoder.py`     -> Wire-format decoding & synthetic `.proto` specs   |
|  - `api_client_generator.py` -> Typed Python (`httpx`+`pydantic`) & TypeScript SDKs|
+-----------------------------------------------------------------------------------+
```

---

## 2. Toolchain Prerequisites & Verification

Verify the availability of reversing and runtime instrumentation tools on the host environment:

| Tool | CLI Check Command | Typical Location | Purpose |
|:---|:---|:---|:---|
| **jadx** | `jadx --version` | PATH (`jadx.bat` / `jadx`) | DEX-to-Java decompiler & resource extractor |
| **Frida** | `frida --version` | PATH (`frida.exe`) | Dynamic binary instrumentation & hook injector |
| **ADB** | `adb version` | Android SDK `platform-tools` | Device communication, shell, and CA management |
| **Python** | `python --version` | Python 3.10+ | Executing helper scripts & client code |
| **Reqable** | Port 9000 listener | `Reqable.exe` | MITM proxy, traffic sniffer & protocol viewer |
| **Proxifier**| GUI / Process check | `Proxifier.exe` | Winsock SPI proxy redirection for stubborn EXEs |
| **dnSpy / ILSpy**| CLI / GUI check | `ilspycmd` | .NET CIL decompiler for managed Windows binaries |

---

## 3. Static Reverse Engineering Workflows

Static analysis exposes endpoints, base URLs, cryptographic signing keys, and request/response models before runtime execution.

### 3.1 Android APK Static Analysis

#### A. Decompilation with `jadx`
```bash
# High-speed decompilation without resource decoding (fastest code search)
jadx -d ./decompiled_code --no-res ./target.apk

# Full decompilation with deobfuscation mode enabled (restores aliases for R8/ProGuard)
jadx -d ./decompiled_app --deobf --deobf-min 3 ./target.apk
```

#### B. Automated API Extraction via `jadx_api_extractor.py`
Use the bundled extraction script to parse Retrofit interfaces, OkHttp builders, hardcoded base URLs, and embedded secrets:

```bash
# Directly extract from APK:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\jadx_api_extractor.py \
  -i ./target.apk \
  -o ./extracted_api.json

# Extract from an existing decompiled source folder:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\jadx_api_extractor.py \
  -i ./decompiled_app \
  -o ./extracted_api.json \
  -f json
```

The script emits structured JSON conforming to the interface contract:
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

#### C. Identifying Request Signatures & Interceptors
1. Search decompiled source code for `okhttp3.Interceptor`:
   ```bash
   grep -rn "implements Interceptor" ./decompiled_app/sources/
   ```
2. Look for cryptographic signing routines:
   - `HmacSHA256`, `HmacSHA1`, `MessageDigest.getInstance("MD5")`
   - Common parameters sorted alphabetically and hashed:
     $$\text{sign} = \text{HMAC-SHA256}(\text{url} + \text{timestamp} + \text{body}, \text{secret})$$

#### D. APK Patching with `apktool` (Alternative to Frida)
If dynamic hooking is blocked by anti-tamper protections:
```bash
# 1. Disassemble APK
apktool d target.apk -o unpacked/

# 2. Inject permissive network security config
cp C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\resources\network_security_config.xml unpacked/res/xml/

# 3. Add android:networkSecurityConfig to <application> in unpacked/AndroidManifest.xml:
#    <application android:networkSecurityConfig="@xml/network_security_config" ...>

# 4. Rebuild and sign
apktool b unpacked/ -o patched.apk
uber-apk-signer -a patched.apk
```

---

### 3.2 Windows Binary (EXE/DLL) Static Analysis

#### A. Application Category Classification
Determine the target technology stack before disassembly:
- **.NET Managed Binary:** Inspect imports for `mscoree.dll`.
  - Tool: Open binary in `dnSpy` or run `ilspycmd -p -o ./decompiled_csharp Target.exe`.
  - Search for `HttpClient`, `RestSharp`, and DTO classes annotated with `[JsonProperty]`.
- **Electron / CEF (Chromium Embedded):**
  - Locate `resources/app.asar` in the installation directory.
  - Unpack bundle:
    ```bash
    npx asar extract "C:\Program Files\TargetApp\resources\app.asar" ./unpacked_asar
    grep -rnE "https?://[a-zA-Z0-9\.\-_]+/api" ./unpacked_asar/
    ```
  - Launch with proxy flags:
    ```bash
    "C:\Program Files\TargetApp\TargetApp.exe" --proxy-server="http://127.0.0.1:9000" --ignore-certificate-errors
    ```
- **Native PE Binary (C/C++, Rust, Go):**
  - Run string extraction: `strings -a Target.exe | grep -E "https?://"`
  - Inspect imported DLLs using `PE-bear` or `dumpbin /imports Target.exe`:
    - `WINHTTP.dll`: `WinHttpOpen`, `WinHttpConnect`, `WinHttpSendRequest`
    - `WININET.dll`: `InternetOpenW`, `HttpSendRequestW`
    - `libcurl.dll`: `curl_easy_init`, `curl_easy_setopt`
  - Open in Ghidra / IDA Pro: Locate cross-references (XREFs) to the discovered endpoint strings.

---

## 4. Dynamic Interception & SSL Unpinning

### 4.1 Android Certificate Trust Matrix

| Android Version | System Trust Storage | Installation Procedure |
|:---|:---|:---|
| **Android 7 – 9** (API 24–28) | `/system/etc/security/cacerts/` | Remount system RW or copy cert via ADB root: `adb push <hash>.0 /system/etc/security/cacerts/` |
| **Android 10 – 13** (API 29–33) | System-as-Root (SAR) Read-Only | Install Reqable CA via **Magisk Module** (mounts tmpfs over `/system/etc/security/cacerts`) |
| **Android 14 – 15** (API 34+) | Conscrypt APEX Module | Bind-mount certificate into APEX container: `mount --bind /data/local/tmp/cacerts /apex/com.android.conscrypt/cacerts/` |

#### Automatic Certificate Hash Computation
```bash
# Calculate OpenSSL subject_hash_old (required by Android)
HASH=$(openssl x509 -inform PEM -subject_hash_old -in reqable_ca.crt | head -1)
cp reqable_ca.crt ${HASH}.0
openssl x509 -inform PEM -text -in reqable_ca.crt -noout >> ${HASH}.0
chmod 644 ${HASH}.0
```

---

### 4.2 Multi-Engine Frida SSL Unpinning (`universal_ssl_unpin.js`)

The bundled script `scripts/universal_ssl_unpin.js` provides comprehensive multi-engine bypass for:
1. Java `X509TrustManager` & `SSLContext.init`
2. OkHttp3 / OkHttp4 `CertificatePinner` (Java and Kotlin mangled methods)
3. Conscrypt & Google Play Services `TrustManagerImpl`
4. Android `NetworkSecurityConfigProvider` & `RootTrustManager`
5. Android WebView `WebViewClient.onReceivedSslError`
6. Flutter BoringSSL ARM64 & ARMv7 memory pattern scan in `libflutter.so`
7. Windows Native WinHTTP (`winhttp.dll`), OpenSSL, and libcurl

#### Execution Commands
```bash
# Android: Spawn process and inject unpinning script immediately
frida -U -f com.target.app -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js

# Android: Attach to an already running app process
frida -U -n com.target.app -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js

# Windows: Spawn desktop executable with unpinning script
frida -f "C:\Program Files\TargetApp\Target.exe" -l C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\universal_ssl_unpin.js
```

---

### 4.3 Android Proxy Routing Mechanisms

1. **Standard Wi-Fi HTTP Proxy:**
   - Configure Android Wi-Fi network settings: Proxy Host = `<Host_PC_IP>`, Proxy Port = `9000`.
2. **ADB Global Proxy Command:**
   ```bash
   adb shell settings put global http_proxy 192.168.1.192:9000
   # To disable:
   adb shell settings put global http_proxy :0
   ```
3. **Reqable Collaborative Mode (TUN / VPN Driver):**
   - For applications that ignore system proxy settings (Flutter, Dart, Go, React Native Hermes, Unreal Engine):
   - Open Reqable Mobile app on Android.
   - Connect in **Collaborative Mode** pairing with Reqable Desktop on port 9000.
   - All IP packets are captured at the virtual network adapter level and forwarded over local Wi-Fi to Desktop Reqable.

---

### 4.4 Windows Desktop Interception (Proxifier)

For Windows applications that do not honor the Windows Internet settings system proxy:

#### Mandatory Loopback Avoidance Configuration
1. Open Proxifier -> **Profile** -> **Proxy Servers**:
   - Add `127.0.0.1:9000` (Protocol: HTTPS or SOCKS5).
2. Configure **Proxification Rules**:
   - **Rule 1 (Reqable Bypass - CRITICAL):**
     - Applications: `Reqable.exe`
     - Action: **Direct**
   - **Rule 2 (Target App Interception):**
     - Applications: `TargetApp.exe; electron.exe; curl.exe`
     - Action: **Proxy 127.0.0.1:9000**
   - **Rule 3 (Default):**
     - Action: **Direct**

---

## 5. Protocol Analysis: REST, Protobuf, gRPC & WebSocket

### 5.1 Protocol Buffers Wire Decoding (`protobuf_decoder.py`)

When reverse engineering mobile and binary applications, network traffic often carries raw Protocol Buffers payloads without available `.proto` schema definitions.

Use `scripts/protobuf_decoder.py` to recursively parse wire types (varint, 64-bit, length-delimited submessages, 32-bit float) and reconstruct clean `.proto` schemas:

```bash
# Decode from hex string:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\protobuf_decoder.py \
  -i "0a0474657374109601" \
  --hex \
  --export-proto ./reconstructed.proto

# Decode from raw binary payload file captured in Reqable:
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\protobuf_decoder.py \
  -i ./payload.bin \
  -o ./decoded_payload.json \
  --export-proto ./schema.proto
```

#### Reconstructed Schema Output Example
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

### 5.2 gRPC Server Reflection & Reqable Proto Mapping
1. **gRPC Reflection:** If the backend implements `grpc.reflection.v1alpha.ServerReflection`, Reqable automatically discovers services and renders payload trees as readable JSON.
2. **Custom Proto Binding:** If reflection is disabled, save the synthetic `.proto` file generated by `protobuf_decoder.py` and bind it in Reqable Desktop via `Settings -> Proto -> Add Spec File`.

### 5.3 WebSocket Stream Inspection
Reqable captures all WebSocket frames (`Opcode 0x1` Text, `Opcode 0x2` Binary):
- Text frames (Socket.IO, STOMP): View formatted JSON in the WebSocket Message Tab.
- Binary frames: Export frame payload to `.bin` and pipe into `protobuf_decoder.py`.

---

## 6. Client Reconstruction Workflows (`api_client_generator.py`)

Transform extracted endpoint specifications into production-grade SDKs:

```bash
python C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\scripts\api_client_generator.py \
  -i ./extracted_api.json \
  -o ./generated_sdk \
  --client-name "ServiceApiClient" \
  --language both
```

### 6.1 Generated Python Client Example (`httpx` + `pydantic`)
```python
import asyncio
from client import ServiceApiClient

async def main():
    async with ServiceApiClient(auth_token="SESSION_TOKEN") as client:
        # Strongly-typed method with path and query parameters
        profile = await client.get_users_profile(id="user_123", details=True)
        print("Profile response:", profile)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 Generated TypeScript Client Example (`fetch`)
```typescript
import { ServiceApiClient } from "./client";

async function run() {
    const client = new ServiceApiClient({
        authToken: "SESSION_TOKEN"
    });

    const profile = await client.getUsersProfile("user_123", { details: true });
    console.log("Profile response:", profile);
}

run();
```

---

## 7. Troubleshooting Matrix

| Problem | Root Cause | Solution |
|:---|:---|:---|
| **App crashes immediately upon Frida spawn** | Anti-Frida detection (scanning for `frida-server` port 27042, `/proc/self/maps`, or thread names) | Use Frida in stealth mode (`frida-server -l 127.0.0.1:44821`), use Magisk Zygisk-Shamiko or Hluda (renamed Frida strings). |
| **Handshake failure on Android 14/15** | System CA installed in `/system/etc/security/cacerts` ignored by Conscrypt APEX | Execute APEX bind-mount inside Zygote namespace: `mount --bind /data/local/tmp/cacerts /apex/com.android.conscrypt/cacerts`. |
| **Flutter HTTPS connections bypass Reqable** | Dart BoringSSL ignores OS proxy and user certs | Use Reqable Collaborative Mode (TUN VPN capture) + inject `universal_ssl_unpin.js` for `libflutter.so` memory pattern scan. |
| **Infinite network loop / crash on Windows** | Proxifier intercepts Reqable's own outbound traffic | Add Proxifier rule: `Application: Reqable.exe -> Action: Direct` (must be placed above target proxy rule). |
| **Protobuf fields show raw hex bytes** | Field contains encrypted or compressed binary payload | Check if bytes start with `1f 8b` (Gzip) or `78 9c` (Zlib); decompress before parsing with `protobuf_decoder.py`. |
| **Retrofit endpoints not found by static scanner** | Obfuscated with R8 / DexGuard with strings encrypted | Use `jadx --deobf` or dump memory strings dynamically via Frida `Memory.scan`. |

---

## 8. Summary of Helper Scripts in `scripts/`

| Script Name | Language | Description & Primary Capabilities |
|:---|:---|:---|
| `universal_ssl_unpin.js` | JavaScript (Frida) | Multi-engine SSL unpinning for Java TrustManager, OkHttp3/4, Conscrypt, WebView, Flutter BoringSSL ARM64/v7, and Windows WinHTTP. |
| `jadx_api_extractor.py` | Python 3 | Decompiles APK via jadx, parses Retrofit annotations, base URLs, XML strings, and secrets into structured JSON. |
| `protobuf_decoder.py` | Python 3 | Pure Python wire-format decoder that recursively parses binary Protobuf payloads without schemas and generates synthetic `.proto` definitions. |
| `api_client_generator.py` | Python 3 | Converts extracted API JSON catalogs into typed async Python (`httpx` + `pydantic`) and TypeScript client SDKs. |
