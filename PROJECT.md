# Project: Production-Grade Web & Binary API Reverse Engineering Skills

## Architecture
This project establishes two production-grade, end-to-end API reverse engineering skills for Antigravity AI agents, integrating the full power of Reqable MITM Proxy, Chrome DevTools MCP, GPM Login anti-detection profiles, and mobile/desktop binary inspection tools:

1. **Web API Reverse Engineering (`api-reverse-engineer`)**:
   - Target: `C:\Users\vutru\.gemini\config\skills\api-reverse-engineer\`
   - Combines GPM Login (Local API port 9495) for stealth anti-fingerprinting browser profiles routed via Reqable Proxy (`127.0.0.1:9000`).
   - Chrome DevTools MCP / CDP for user automation and interaction.
   - Reqable MCP for live traffic capture, filtering, packet tampering (rewrite/breakpoints), and Python scripting.
   - Session extraction (JWT, cookies, CSRF) adapted from `browser-login-capture` and guest bootstrapping from `agent-reach`.
   - 4 turnkey helper scripts in `scripts/`: `gpm_reqable_launcher.py`, `traffic_capture.py`, `auth_extractor.py`, `curl_to_client.py`, maintaining compatibility with `api_analyzer.py` and `har_to_openapi.py`.

2. **Mobile and Binary API Reverse Engineering (`binary-api-reverse-engineer`)**:
   - Target: `C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\`
   - Static analysis: `jadx` CLI/GUI decompilation for Android APKs (extracting Retrofit/OkHttp endpoints, base URLs, secrets); `dnSpy`/`ILSpy` (.NET) and `Ghidra` (native PE) for Windows EXEs.
   - Dynamic interception & SSL Unpinning: Multi-engine Frida hook scripts (`universal_ssl_unpin.js`) covering Java `X509TrustManager`, OkHttp3/4, Android 14/15 Conscrypt APEX bind mounts, Flutter BoringSSL ARM64 pattern scanning in `libflutter.so`, and Windows WinHTTP/OpenSSL unpinning.
   - Protocol decoding: Wire-level raw Protobuf recursive decoding without `.proto` files, synthetic `.proto` generation, gRPC reflection, and WebSocket frame extraction.
   - 4 turnkey helper scripts in `scripts/`: `universal_ssl_unpin.js`, `jadx_api_extractor.py`, `protobuf_decoder.py`, `api_client_generator.py`.

3. **Empirical Validation & Testing**:
   - Web API workflow validation against a real-world public web target, traffic capture, and client synthesis.
   - Binary reverse engineering validation against an open-source APK target (decompilation, endpoint extraction, proxy configuration).
   - Python 3.13 compilation and lint verification for all scripts.

---

## Code Layout
```
C:\Users\vutru\.gemini\config\skills\
├── api-reverse-engineer/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── gpm_reqable_launcher.py
│   │   ├── traffic_capture.py
│   │   ├── auth_extractor.py
│   │   ├── curl_to_client.py
│   │   ├── api_analyzer.py (existing, retained & enhanced)
│   │   └── har_to_openapi.py (existing, retained & enhanced)
│   └── resources/
│       └── api_doc_template.md
│
└── binary-api-reverse-engineer/
    ├── SKILL.md
    └── scripts/
        ├── universal_ssl_unpin.js
        ├── jadx_api_extractor.py
        ├── protobuf_decoder.py
        └── api_client_generator.py
```

---

## Feature Inventory
Every inventoried feature from the survey phase is assigned to a specific milestone.

| # | Feature ID | Feature Name | Description | Milestone | Source |
|---|------------|--------------|-------------|-----------|--------|
| 1 | R1-F1 | Web Antigravity Frontmatter | Valid YAML frontmatter with precise triggers, descriptions, and keywords | M1 | Survey 1 |
| 2 | R1-F2 | Web Architecture Documentation | End-to-end topology: GPM Browser -> Reqable Proxy (:9000) -> Target APIs | M1 | Survey 1 |
| 3 | R1-F3 | Reqable MCP Web Integration | MCP tool usage guide for `proxy_set`, `capture_live_*`, `capture_rewrite_*`, `capture_script_*` | M1 | Survey 1, 2 |
| 4 | R1-F4 | GPM Login Anti-Detect Guide | Stealth browser profile creation with `raw_proxy: 127.0.0.1:9000` and CDP attachment | M1 | Survey 1, 2 |
| 5 | R1-F5 | 6-Phase Web Reverse Workflow | Recon, Environment, Traffic Capture, Authentication, Replay/Tampering, Client Generation | M1 | Survey 1 |
| 6 | R1-F6 | Bot Defense & Anti-Fingerprint | Cloudflare Turnstile, Akamai, Datadome, FingerprintJS mitigation workflows | M1 | Survey 1 |
| 7 | R1-F7 | Web Troubleshooting Table | Error matrix for SSL handshakes, 401/403/429, CORS, API Service disabled | M1 | Survey 1, 2 |
| 8 | R1-S1 | `gpm_reqable_launcher.py` | CLI automation to create/launch GPM profile routed through Reqable proxy | M1 | Survey 1 |
| 9 | R1-S2 | `traffic_capture.py` | CLI automation for live Reqable capture, filtering, and JSON export | M1 | Survey 1, 2 |
| 10 | R1-S3 | `auth_extractor.py` | CLI script for JWT decoding, cookie jar parsing, CSRF extraction, `.env` output | M1 | Survey 1 |
| 11 | R1-S4 | `curl_to_client.py` | CLI script converting cURL/HAR to typed Python (`requests`/`httpx`) & TypeScript clients | M1 | Survey 1 |
| 12 | R2-F1 | Binary Antigravity Frontmatter | Standalone YAML frontmatter with triggers for mobile/binary API reversing | M2 | Survey 3 |
| 13 | R2-F2 | Android Static jadx Workflow | Retrofit 2/OkHttp interface parsing, base URLs, headers, models, secrets | M2 | Survey 3 |
| 14 | R2-F3 | Windows Static Reversing Guide | .NET dnSpy/ILSpy, Electron asar unpacking, Ghidra/PE-bear native inspection | M2 | Survey 2, 3 |
| 15 | R2-F4 | Android CA Certificate Trust | Android 7-13 User/System store, Magisk tmpfs, Android 14/15 APEX bind-mounts | M2 | Survey 2, 3 |
| 16 | R2-F5 | Multi-Engine Frida Unpinning | Hooking Java X509TrustManager, OkHttp3/4, Conscrypt, Flutter BoringSSL ARM64 | M2 | Survey 2, 3 |
| 17 | R2-F6 | Windows Dynamic Interception | Proxifier loopback-safe rules (`Reqable -> Direct`, `Target -> 127.0.0.1:9000`), Frida WinHTTP | M2 | Survey 2, 3 |
| 18 | R2-F7 | Protocol Analysis (Protobuf/gRPC) | Raw wire-level Protobuf decoding without `.proto`, gRPC reflection, WebSocket frames | M2 | Survey 2, 3 |
| 19 | R2-F8 | Client Reconstruction Workflow | Generating typed Python (`httpx`/`pydantic`) and TypeScript SDKs from mobile specs | M2 | Survey 3 |
| 20 | R2-F9 | Binary Troubleshooting Table | Mitigation for anti-Frida, root detection, broken APEX mounts, crash loops | M2 | Survey 2, 3 |
| 21 | R2-S1 | `universal_ssl_unpin.js` | Turnkey Frida script bypassing Java, OkHttp, Flutter BoringSSL, and WebView pinning | M2 | Survey 3 |
| 22 | R2-S2 | `jadx_api_extractor.py` | Python CLI to decompile APK with jadx and extract all API contracts to JSON | M2 | Survey 3 |
| 23 | R2-S3 | `protobuf_decoder.py` | Pure Python wire decoder for Protobuf payloads without schemas + `.proto` generator | M2 | Survey 3 |
| 24 | R2-S4 | `api_client_generator.py` | Python CLI generator creating async Python and TypeScript client SDKs from schemas | M2 | Survey 3 |
| 25 | M3-V1 | Script Syntax & Lint Verification | Compile and verify all 8 scripts on host Python 3.13 / Node / Frida | M3 | Testing Track |
| 26 | M3-V2 | Live Web API Validation | Execute end-to-end web workflow on a public API target with client generation | M3 | Testing Track |
| 27 | M3-V3 | Static APK Validation | Execute `jadx_api_extractor.py` on an open-source APK target and verify output | M3 | Testing Track |
| 28 | M3-V4 | Forensic Integrity Audit | Complete forensic integrity audit of all created skills, scripts, and documentation | M3 | Testing Track |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Web API Reverse Engineering Skill Upgrade & Scripts | Implement all R1 features (R1-F1..F7) and scripts (R1-S1..S4) in `C:\Users\vutru\.gemini\config\skills\api-reverse-engineer\` | Survey complete | DONE |
| M2 | Mobile & Binary API Reverse Engineering Skill & Scripts | Implement all R2 features (R2-F1..F9) and scripts (R2-S1..S4) in `C:\Users\vutru\.gemini\config\skills\binary-api-reverse-engineer\` | Survey complete | PLANNED |
| M3 | End-to-End Validation, Empirical Testing & Forensic Audit | Execute M3-V1..V4: Python compilation checks, live web API test, APK extraction test, forensic integrity audit | M1, M2 | PLANNED |

---

## Interface Contracts

### Script Output Schemas
1. **`traffic_capture.py` / `capture_live_filter` JSON Schema**:
   - Emits structured array of HTTP transactions: `[{"id": str, "method": str, "url": str, "request_headers": dict, "request_body": str/null, "status_code": int, "response_headers": dict, "response_body": str/null}]`.
   - Compatible as direct input to `curl_to_client.py`, `auth_extractor.py`, and `api_analyzer.py`.

2. **`jadx_api_extractor.py` JSON Schema**:
   - Emits structured endpoint catalogue: `{"endpoints": [{"method": str, "path": str, "base_url": str, "headers": dict, "query_params": [str], "body_type": str, "source_file": str, "source_line": int}], "extracted_keys": [{"key": str, "type": str, "source": str}]}`.
   - Compatible as direct input to `api_client_generator.py`.

3. **`protobuf_decoder.py` Output Schema**:
   - Emits decoded JSON tree representation of wire types and fields: `{"fields": {"field_number": {"wire_type": int, "value": any}}, "synthetic_proto": str}`.
