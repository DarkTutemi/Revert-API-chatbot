---
name: api-reverse-engineer
description: >-
  Production-grade Web API reverse engineering framework. Use when extracting APIs,
  reverse engineering web service backends, intercepting encrypted traffic via Reqable MITM Proxy,
  evading bot defense and anti-bot fingerprinting via GPM Login stealth profiles,
  capturing JWT/session cookies/CSRF authentication, replaying or tampering requests,
  or synthesizing production-ready Python/TypeScript client SDKs and OpenAPI 3.0 specs.
---

# Web API Reverse Engineering Skill

A comprehensive, production-grade methodology and automation toolkit for reverse engineering HTTP/1.1, HTTP/2, WebSocket, and RESTful APIs from any modern web application.

This skill integrates:
- **Reqable MITM Proxy (`reqable-mcp` on `127.0.0.1:9000`)**: C++ native inspection engine, live traffic capture, packet filtering, request rewrite rules, breakpoints, and dynamic Python script addons (`reqable.py`).
- **GPM Login Stealth Browser (`gpmlogin` Local API on `localhost:9495`)**: Anti-detection browser profiles spoofing Canvas, WebGL, Audio, ClientRects, Fonts, and WebRTC, pre-configured to route all traffic through Reqable.
- **Chrome DevTools MCP (`chrome-devtools`)**: Direct browser control, headless DOM manipulation, event simulation, and CDP debugging.
- **Authentication Capture Engine**: Ephemeral in-memory extraction of JWT claims, session cookies, and CSRF tokens with automatic client token-refresh mechanisms.
- **Turnkey Automation Scripts (`scripts/`)**: CLI tools for profile launching, traffic recording, auth extraction, cURL-to-client synthesis, and OpenAPI generation.

---

## 1. System Architecture & Traffic Flow

The reverse engineering engine bridges anti-detection browser automation with proxy-level packet inspection:

```
+─────────────────────────────────────────────────────────────────────────────+
| GPM Login Stealth Profile (Chromium)                                        |
| - Anti-Fingerprint: Noise on Canvas, WebGL, Audio, ClientRects, Fonts       |
| - Isolated Cookie/Session Storage                                           |
| - Configured Proxy: http://127.0.0.1:9000                                   |
| - Controlled via CDP (remote_debugging_port / websocket_debugging_url)      |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                         All HTTPS / WebSocket Traffic
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Reqable MITM Proxy & Engine (127.0.0.1:9000)                                |
| - SSL Decryption (Reqable Root CA)                                          |
| - Live Inspection & Filtering (capture_live_filter)                          |
| - Active Tampering (capture_rewrite_*, capture_breakpoint_*)                |
| - Python Script Addons (onRequest / onResponse via reqable.py)              |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                         Decrypted & Forwarded Traffic
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Target Web APIs (Cloudflare / Akamai / Custom Endpoints)                     |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
                      Captured Transactions / cURL Logs
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| Downstream Synthesis Toolkit (scripts/)                                      |
| - auth_extractor.py: In-memory JWT/cookie extraction & .env synthesis        |
| - curl_to_client.py: Typed Python (requests/httpx) & TypeScript clients      |
| - har_to_openapi.py: Machine-readable OpenAPI 3.0 specification             |
| - api_analyzer.py: Endpoint categorization & Markdown documentation         |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Tool Collaboration Matrix

| Tool / Subsystem | Primary Capability | Key Commands / API Calls |
| :--- | :--- | :--- |
| **`reqable-mcp`** | Proxy control & live traffic capture | `capture_live_set_enabled`, `capture_live_filter`, `capture_live_get_by_id`, `capture_live_generate_curl`, `capture_live_compose` |
| **`reqable-mcp`** | Rules & packet tampering | `capture_rewrite_create`, `capture_breakpoint_create`, `capture_script_create` |
| **`gpmlogin` Local API** | Anti-detection profile management | `GET /profiles`, `POST /profiles/create` (`raw_proxy: 127.0.0.1:9000`), `GET /profiles/start/{id}`, `GET /profiles/stop/{id}` |
| **`chrome-devtools`** | Headless driving & DOM interaction | `navigate_page`, `click`, `fill`, `evaluate_script`, `list_network_requests` |
| **`scripts/gpm_reqable_launcher.py`** | Stealth browser spawner | CLI utility creating GPM profiles with noise injection routed through Reqable proxy |
| **`scripts/traffic_capture.py`** | Live traffic recording | CLI utility capturing live Reqable streams and exporting standardized JSON |
| **`scripts/auth_extractor.py`** | Credential & token parsing | Extracts JWT claims, session cookies, and CSRF tokens into `.env` and wrappers |
| **`scripts/curl_to_client.py`** | Client SDK synthesis | Converts cURL / transactions to typed Python (`requests`/`httpx`) and TypeScript |
| **`scripts/api_analyzer.py`** | Endpoint cataloging | Generates structured Markdown API documentation from traffic JSON |
| **`scripts/har_to_openapi.py`** | OpenAPI 3.0 generation | Emits OpenAPI 3.0 YAML/JSON specification with schema inference |

---

## 3. End-to-End 6-Phase Reverse Engineering Workflow

```
Phase 1: Recon & Bot Defense Profiling
   │
   ▼
Phase 2: Environment Setup & Proxy Attachment
   │
   ▼
Phase 3: Live Traffic Capture & Filtering
   │
   ▼
Phase 4: Authentication & Guest Session Bootstrapping
   │
   ▼
Phase 5: Request Replay, Tampering & Signature Emulation
   │
   ▼
Phase 6: Schema Extraction & Client Code Generation
```

### Phase 1: Reconnaissance & Bot Defense Profiling

1. **Evaluate Target Surface**:
   - Inspect the landing page, AJAX calls, and public script bundles.
   - Profile the Web Application Firewall (WAF) and bot detection mechanisms:
     * **Cloudflare Turnstile / Challenge**: Detect `cf-ray`, `cf_clearance`, or Turnstile iframe widgets.
     * **Akamai Bot Manager**: Detect `_abck`, `bm_sz` cookies or sensor data scripts.
     * **Datadome**: Detect `datadome` cookie, 403 JSON payloads, and CAPTCHA popups.
     * **FingerprintJS / CreepJS**: Look for client-side canvas, WebGL, or audio hash calculations in vendor bundles.
2. **Select Browser Architecture**:
   - For basic websites without fingerprinting: Use Chrome DevTools MCP directly.
   - For protected sites (Cloudflare, Akamai, Datadome): **Must use GPM Login Stealth Profile** routed through Reqable proxy (`127.0.0.1:9000`).

---

### Phase 2: Environment Setup & Proxy Attachment

#### Step 1: Ensure Reqable Proxy is Listening
Reqable listens on port 9000 (default: `127.0.0.1:9000` or local LAN IP `192.168.1.192:9000`).
Verify proxy availability:
```bash
curl -I http://127.0.0.1:9000/
```
Ensure the Reqable Root CA certificate is installed and trusted in the OS Root Certificate Store.

#### Step 2: Spawn GPM Stealth Profile with Reqable Proxy Routing
Execute `gpm_reqable_launcher.py` to create and launch an anti-detection profile:
```bash
python "<skill_dir>/scripts/gpm_reqable_launcher.py" --name "Target_ReverseEng" --proxy "http://127.0.0.1:9000" --start
```
Output returns:
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

#### Step 3: Attach Browser Automation (CDP / Chrome DevTools)
Connect to the running profile via CDP WebSocket URL or port `54321` to drive navigation and user interactions.

---

### Phase 3: Live Traffic Capture & Filtering

#### Step 1: Enable Reqable Live Capture
Via `reqable-mcp`:
```json
{
  "tool": "capture_live_set_enabled",
  "arguments": { "enabled": true }
}
```

#### Step 2: Simulate User Navigation & Actions
Drive user interaction to trigger target AJAX, GraphQL, or REST endpoints:
- Page transitions, pagination clicks, search inputs, infinite scroll triggers.
- Form submissions and modal popups.

#### Step 3: Filter & Record Traffic
Run `traffic_capture.py` to record transactions, filtering out static noise:
```bash
python "<skill_dir>/scripts/traffic_capture.py" --host "127.0.0.1" --port 9000 --domain "api.target.com" --duration 20 --output "captured_traffic.json"
```

Or query via `reqable-mcp`:
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

### Phase 4: Authentication & Guest Session Bootstrapping

Modern web APIs rely on either anonymous guest sessions or authenticated user credentials.

#### 1. Guest Session Bootstrapping (Zero-Login Public APIs)
Many platforms (e.g. Xueqiu, Bilibili, Reddit, Twitter) provide full read access if an initial handshake is executed to acquire guest cookies:
1. Issue a `GET` request to the landing page or a bootstrap endpoint (`/`, `/api/init`, `/v1/guest/token`).
2. Extract the returned `Set-Cookie` headers (e.g., `xq_a_token`, `guest_id`, `anon_id`).
3. Store cookies in the HTTP client session jar. Subsequent API calls succeed without user login credentials.

#### 2. Authenticated Session & Token Extraction
Run `auth_extractor.py` against the captured traffic:
```bash
python "<skill_dir>/scripts/auth_extractor.py" --input "captured_traffic.json" --output "auth_config.json" --env-file ".env" --wrapper "auth_session.py"
```

Extracted Artifacts:
- **JWT Claims**: Decodes payload claims (`sub`, `iss`, `roles`, `exp`), calculating token Time-To-Live (TTL) and detecting expiration.
- **Session Cookies**: Formats all `Set-Cookie` directives into clean dictionary pairs.
- **CSRF Tokens**: Detects headers (`x-csrf-token`, `x-xsrf-token`) and cookies (`XSRF-TOKEN`).
- **Sanitized `.env`**: Emits ready-to-load environment variables (`API_ACCESS_TOKEN`, `API_REFRESH_TOKEN`, `API_COOKIE_JAR`).

---

### Phase 5: Request Replay, Tampering & Signature Emulation

Verify endpoint behavior and test parameter variations using Reqable's traffic manipulation engines.

#### 1. Request Replay & Composition
To re-test an intercepted request with modified parameters via `reqable-mcp`:
```json
{
  "tool": "capture_live_compose",
  "arguments": {
    "id": "1042"
  }
}
```

Or export as a standalone cURL command:
```json
{
  "tool": "capture_live_generate_curl",
  "arguments": {
    "id": "1042"
  }
}
```

#### 2. Mocking & Response Rewriting
To simulate server errors (500), rate limiting (429), or mock response payloads without backend access:
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

#### 3. Real-Time Breakpoint Debugging
Freeze outgoing requests or incoming responses to inspect or modify headers before forwarding:
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

#### 4. Dynamic Signature Calculation (Reqable Python Scripting)
When APIs enforce cryptographic request signing (MD5 query sign, HMAC-SHA256, AES payload encryption), attach a Reqable Python script (`capture_script_create`).

Reqable executes Python scripts via isolated subprocess IPC (`onRequest` and `onResponse`):

```python
# reqable_script_sign.py
from reqable import *
import hashlib
import time

def onRequest(context: Context, request: HttpRequest) -> HttpRequest:
    # 1. Add current timestamp
    ts = str(int(time.time() * 1000))
    request.queries["_t"] = ts
    
    # 2. Sort query parameters and calculate MD5 signature
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

Register the script via `reqable-mcp`:
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

### Phase 6: Schema Extraction & Client Code Generation

#### 1. Generate Structured Markdown API Documentation
```bash
python "<skill_dir>/scripts/api_analyzer.py" --input "captured_traffic.json" --output "api_documentation.md"
```
Produces an itemized catalog of all discovered endpoints, normalized path patterns (e.g. `/api/v1/users/:id`), query parameter schemas, and request/response body schemas.

#### 2. Generate OpenAPI 3.0 Specification
```bash
python "<skill_dir>/scripts/har_to_openapi.py" --input "captured_traffic.json" --output "openapi.yaml" --format yaml
```
Emits standard OpenAPI 3.0 specification ready for import into Swagger, Postman, or code generators.

#### 3. Synthesize Production API Client SDK
Convert captured cURL commands or traffic JSON into production-grade Python or TypeScript clients:

**Generate Python Client (`requests` sync):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang python-requests --output "target_client.py"
```

**Generate Python Client (`httpx` async):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang python-httpx --output "async_target_client.py"
```

**Generate TypeScript Client (`fetch`):**
```bash
python "<skill_dir>/scripts/curl_to_client.py" --input "captured_traffic.json" --lang typescript --output "TargetClient.ts"
```

**Client Code Features**:
- **Header Hygiene**: Strips HTTP/2 pseudo-headers (`:authority`, `:path`, `:method`) and unsupported compression headers (`br`, `zstd`).
- **Token Parameterization**: Converts hardcoded bearer tokens into constructor parameters and environment variable fallbacks (`API_ACCESS_TOKEN`).
- **Automated 401 Interception**: Built-in hook to trigger token refresh and retry failed requests.

---

## 4. Anti-Detection & Bot Mitigation Strategies

Modern WAFs employ layered bot defense. Apply these strategies when encountering blocks:

| Defense Layer | Mechanism | Mitigation Strategy |
| :--- | :--- | :--- |
| **Browser Fingerprinting** | Canvas, WebGL, AudioContext, Font hashing, ClientRects | Launch browser via `gpm_reqable_launcher.py`. GPM Login injects mathematical noise into hardware APIs, preventing unique device identification. |
| **WAF IP Reputation** | Datadome / Cloudflare rate limits on residential/datacenter IPs | Configure upstream residential/mobile proxy in GPM (`raw_proxy`) or configure upstream proxy in Reqable. |
| **Cloudflare Turnstile** | Cryptographic proof-of-work in hidden iframe | Keep GPM browser window open in foreground; allow genuine JavaScript execution; never use pure headless flags (`--headless=new` triggers Turnstile blocks). |
| **HTTP/2 Fingerprinting** | JA3, JA4, and HTTP/2 SETTINGS frame fingerprinting | Route client requests through standard Python `httpx` with HTTP/2 enabled, or replicate exact browser headers using GPM's browser engine. |
| **Header Hygiene** | Server drops requests containing `:authority` or uppercase headers | Use `curl_to_client.py` which automatically purges HTTP/2 pseudo-headers and dangerous transport headers. |

---

## 5. Diagnostics & Troubleshooting Matrix

| Symptom / Error | Root Cause | Resolution Procedure |
| :--- | :--- | :--- |
| **SSL Handshake Failed / Certificate Invalid** | Browser or client does not trust Reqable Root CA | Open Reqable -> Certificate Manager -> Install Root CA in "Trusted Root Certification Authorities" (Windows) or import into browser profile. |
| **HTTP 401 Unauthorized** | Token expired or auth headers missing | Run `auth_extractor.py` to check JWT `_is_expired` and `_ttl_seconds`. Re-run login capture or guest bootstrap flow to obtain fresh credentials. |
| **HTTP 403 Forbidden / Cloudflare Challenge** | Bot detection triggered by headless browser or abnormal fingerprint | Terminate native Chrome. Start a stealth profile with `gpm_reqable_launcher.py`. Avoid automated mouse teleportation; simulate human delays. |
| **HTTP 429 Too Many Requests** | Rate limit exceeded on IP or user token | Inspect `X-RateLimit-Reset` and `Retry-After` headers. Implement exponential backoff in client code. Rotate GPM proxy IP if IP-limited. |
| **Port 9495 Connection Refused (GPM API)** | GPM Login application is closed or port occupied | Start GPM Login Desktop application. If port 9495 is busy, check `%LOCALAPPDATA%\GPMLogin\http.port` for dynamically assigned port. |
| **Port 9000 Connection Refused (Reqable)** | Reqable application or proxy service is stopped | Launch Reqable Desktop and ensure Proxy Status is active (green indicator at bottom bar). |
| **Empty Capture Traffic in `traffic_capture.py`** | Proxy routing bypassed or live capture disabled | Check `raw_proxy: http://127.0.0.1:9000` in GPM profile. Ensure `capture_live_set_enabled` is set to `true`. |
| **Encoding Error / Garbage Response Body** | Response compressed with `zstd` or `br` | Strip `Accept-Encoding: br, zstd` in request headers, or enable automatic decompression in Reqable / `httpx`. |
