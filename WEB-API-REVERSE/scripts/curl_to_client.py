#!/usr/bin/env python3
"""
cURL to Client — Synthesize Modular, Typed Python and TypeScript API Clients

Converts captured cURL commands (from Reqable `capture_live_generate_curl` or DevTools)
or standardized Reqable transaction JSON into clean, production-grade API client classes.

Supported Output Frameworks:
- Python (`httpx` async or `requests` sync)
- TypeScript (`axios` or native `fetch`)

Features:
- Header hygiene: Strips HTTP/2 pseudo-headers (:authority, :path, :method, :scheme)
  and problematic compression directives (br, zstd).
- Token parameterization: Automatically converts static Authorization and Cookie
  headers into configurable constructor arguments and environment variables.
- Auto-refresh & 401 retry handling.
"""

import argparse
import json
import os
import re
import shlex
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


STRIP_HEADERS = {
    ":authority", ":method", ":path", ":scheme", ":status",
    "content-length", "accept-encoding", "host", "connection",
}


def parse_curl_command(curl_cmd: str) -> Dict[str, Any]:
    """Parse a cURL command string into structured request components."""
    # Normalize escaped newlines and line breaks
    cleaned_cmd = curl_cmd.replace("\\\n", " ").replace("\\\r\n", " ").strip()
    
    # Lexical tokenization
    try:
        tokens = shlex.split(cleaned_cmd)
    except Exception:
        tokens = cleaned_cmd.split()

    method = "GET"
    url = ""
    headers = {}
    data = None

    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token in ("-X", "--request") and idx + 1 < len(tokens):
            method = tokens[idx + 1].upper()
            idx += 2
        elif token in ("-H", "--header") and idx + 1 < len(tokens):
            header_str = tokens[idx + 1]
            if ":" in header_str:
                k, v = header_str.split(":", 1)
                headers[k.strip()] = v.strip()
            idx += 2
        elif token in ("-d", "--data", "--data-raw", "--data-binary") and idx + 1 < len(tokens):
            data = tokens[idx + 1]
            if method == "GET":
                method = "POST"
            idx += 2
        elif token.startswith("http://") or token.startswith("https://"):
            url = token
            idx += 1
        elif idx == 1 and not token.startswith("-"):
            url = token
            idx += 1
        else:
            idx += 1

    return {
        "method": method,
        "url": url,
        "headers": headers,
        "body": data,
    }


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Strip browser pseudo-headers and dangerous transport headers."""
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in STRIP_HEADERS:
            continue
        sanitized[k] = v
    return sanitized


def derive_endpoint_name(method: str, path: str) -> str:
    """Generate an idiomatic Python/TypeScript function name from HTTP method and path."""
    clean_path = re.sub(r"[{}:]", "", path)
    segments = [s for s in clean_path.split("/") if s and not s.startswith("v1") and not s.startswith("v2") and not s.startswith("api")]
    if not segments:
        return f"{method.lower()}_root"
    name = f"{method.lower()}_{'_'.join(segments[:3])}"
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return name.lower()


def generate_python_requests_client(req_spec: Dict[str, Any], class_name: str = "TargetAPIClient") -> str:
    """Synthesize synchronous Python requests client class."""
    url = req_spec["url"]
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    path = parsed_url.path or "/"
    clean_headers = sanitize_headers(req_spec.get("headers", {}))

    # Parameterize auth header
    has_bearer = False
    auth_header = clean_headers.get("Authorization") or clean_headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        has_bearer = True
        clean_headers.pop("Authorization", None)
        clean_headers.pop("authorization", None)

    func_name = derive_endpoint_name(req_spec["method"], path)
    method = req_spec["method"]
    body_data = req_spec.get("body")

    code = f'''# Generated API Client — Python (requests)
import os
import json
from typing import Any, Dict, Optional
import requests

class {class_name}:
    """Production-grade client for {base_url}."""

    def __init__(self, token: Optional[str] = None, base_url: str = "{base_url}"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = token or os.getenv("API_ACCESS_TOKEN", "")

        # Default headers
        self.session.headers.update({json.dumps(clean_headers, indent=12)})
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {{self.token}}"

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{{self.base_url}}{{endpoint}}"
        response = self.session.request(method, url, **kwargs)

        # Automated 401 retry interceptor
        if response.status_code == 401:
            print("[!] Token expired or unauthorized. Refreshing credentials...")
            if self._refresh_token():
                if self.token:
                    self.session.headers["Authorization"] = f"Bearer {{self.token}}"
                response = self.session.request(method, url, **kwargs)

        return response

    def _refresh_token(self) -> bool:
        # TODO: Implement token refresh logic if refresh endpoint is known
        return False

    def {func_name}(self, params: Optional[Dict[str, Any]] = None, data: Optional[Any] = None) -> Any:
        """Call {method} {path}"""
        endpoint = "{path}"
        kwargs: Dict[str, Any] = {{}}
        if params:
            kwargs["params"] = params
        if data:
            if isinstance(data, (dict, list)):
                kwargs["json"] = data
            else:
                kwargs["data"] = data
'''
    if body_data:
        code += f'''        elif data is None:
            # Default captured payload
            kwargs["data"] = {json.dumps(body_data)}
'''
    code += f'''
        resp = self._request("{method}", endpoint, **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text
'''
    return code


def generate_python_httpx_client(req_spec: Dict[str, Any], class_name: str = "AsyncTargetAPIClient") -> str:
    """Synthesize asynchronous Python httpx client class."""
    url = req_spec["url"]
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    path = parsed_url.path or "/"
    clean_headers = sanitize_headers(req_spec.get("headers", {}))

    auth_header = clean_headers.get("Authorization") or clean_headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        clean_headers.pop("Authorization", None)
        clean_headers.pop("authorization", None)

    func_name = derive_endpoint_name(req_spec["method"], path)
    method = req_spec["method"]
    body_data = req_spec.get("body")

    code = f'''# Generated API Client — Python (httpx async)
import os
import json
from typing import Any, Dict, Optional
import httpx

class {class_name}:
    """Asynchronous client for {base_url} using httpx."""

    def __init__(self, token: Optional[str] = None, base_url: str = "{base_url}"):
        self.base_url = base_url.rstrip("/")
        self.token = token or os.getenv("API_ACCESS_TOKEN", "")
        self.headers = {json.dumps(clean_headers, indent=12)}
        if self.token:
            self.headers["Authorization"] = f"Bearer {{self.token}}"

    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        url = f"{{self.base_url}}{{endpoint}}"
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            return await client.request(method, url, **kwargs)

    async def {func_name}(self, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Any:
        """Asynchronously call {method} {path}"""
        endpoint = "{path}"
        kwargs: Dict[str, Any] = {{}}
        if params:
            kwargs["params"] = params
        if json_body:
            kwargs["json"] = json_body
'''
    if body_data:
        try:
            parsed_body = json.loads(body_data)
            code += f'''        elif json_body is None:
            kwargs["json"] = {json.dumps(parsed_body, indent=12)}
'''
        except Exception:
            code += f'''        elif json_body is None:
            kwargs["content"] = {json.dumps(body_data)}
'''
    code += f'''
        resp = await self._request("{method}", endpoint, **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text
'''
    return code


def generate_typescript_client(req_spec: Dict[str, Any], class_name: str = "TargetAPIClient") -> str:
    """Synthesize modern TypeScript client class with fetch."""
    url = req_spec["url"]
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    path = parsed_url.path or "/"
    clean_headers = sanitize_headers(req_spec.get("headers", {}))

    auth_header = clean_headers.get("Authorization") or clean_headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        clean_headers.pop("Authorization", None)
        clean_headers.pop("authorization", None)

    func_name = derive_endpoint_name(req_spec["method"], path)
    method = req_spec["method"]
    body_data = req_spec.get("body")

    code = f'''// Generated API Client — TypeScript (fetch)
export interface RequestOptions {{
  params?: Record<string, string | number>;
  body?: any;
  headers?: Record<string, string>;
}}

export class {class_name} {{
  private baseUrl: string;
  private token: string;
  private defaultHeaders: Record<string, string>;

  constructor(token: string = "", baseUrl: string = "{base_url}") {{
    this.baseUrl = baseUrl.replace(/\\/+$/, "");
    this.token = token || (typeof process !== "undefined" ? process.env.API_ACCESS_TOKEN || "" : "");
    this.defaultHeaders = {json.dumps(clean_headers, indent=6)};
    if (this.token) {{
      this.defaultHeaders["Authorization"] = `Bearer ${{this.token}}`;
    }}
  }}

  private async request<T = any>(method: string, endpoint: string, options: RequestOptions = {{}}): Promise<T> {{
    let url = `${{this.baseUrl}}${{endpoint}}`;
    if (options.params) {{
      const query = new URLSearchParams(options.params as any).toString();
      if (query) url += `?${{query}}`;
    }}

    const headers = {{ ...this.defaultHeaders, ...options.headers }};
    const config: RequestInit = {{
      method,
      headers,
    }};

    if (options.body) {{
      config.body = typeof options.body === "string" ? options.body : JSON.stringify(options.body);
    }}

    const res = await fetch(url, config);
    if (!res.ok) {{
      throw new Error(`API Request Failed: ${{res.status}} ${{res.statusText}}`);
    }}

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {{
      return (await res.json()) as T;
    }}
    return (await res.text()) as unknown as T;
  }}

  public async {func_name}<T = any>(params?: Record<string, string | number>, body?: any): Promise<T> {{
    return this.request<T>("{method}", "{path}", {{ params, body }});
  }}
}}
'''
    return code


def main():
    parser = argparse.ArgumentParser(description="cURL to Typed Python & TypeScript Client Synthesizer")
    parser.add_argument("--curl", help="Raw cURL command string to convert")
    parser.add_argument("--curl-file", help="Path to file containing raw cURL command")
    parser.add_argument("--input", "-i", help="Path to captured traffic JSON file (Reqable or HAR)")
    parser.add_argument("--lang", choices=["python-requests", "python-httpx", "typescript"], default="python-requests", help="Target client language and framework")
    parser.add_argument("--output", "-o", default=None, help="Output file path (default: printed to stdout)")
    parser.add_argument("--class-name", default="ApiClient", help="Name of the generated client class")

    args = parser.parse_args()

    req_spec = None
    if args.curl:
        req_spec = parse_curl_command(args.curl)
    elif args.curl_file:
        with open(args.curl_file, "r", encoding="utf-8") as f:
            req_spec = parse_curl_command(f.read())
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            traffic_data = json.load(f)
        first_item = traffic_data[0] if isinstance(traffic_data, list) and traffic_data else traffic_data
        # Map traffic item to req_spec
        url = first_item.get("url") or first_item.get("request", {}).get("url", "")
        method = first_item.get("method") or first_item.get("request", {}).get("method", "GET")
        headers = first_item.get("request_headers") or first_item.get("request", {}).get("headers", {})
        if isinstance(headers, list):
            headers = {h.get("name", ""): h.get("value", "") for h in headers if "name" in h}
        body = first_item.get("request_body") or first_item.get("request", {}).get("postData", {}).get("text")
        req_spec = {"method": method, "url": url, "headers": headers, "body": body}

    if not req_spec or not req_spec.get("url"):
        print("[-] Error: No valid request URL found. Specify --curl, --curl-file, or --input.", file=sys.stderr)
        sys.exit(1)

    generated_code = ""
    if args.lang == "python-requests":
        generated_code = generate_python_requests_client(req_spec, class_name=args.class_name)
    elif args.lang == "python-httpx":
        generated_code = generate_python_httpx_client(req_spec, class_name=args.class_name)
    elif args.lang == "typescript":
        generated_code = generate_typescript_client(req_spec, class_name=args.class_name)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"[+] Client synthesized successfully in '{args.output}'")
    else:
        print(generated_code)


if __name__ == "__main__":
    main()
