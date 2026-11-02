#!/usr/bin/env python3
"""
api_client_generator.py

CLI tool that scaffolds production-grade, typed API Client SDKs in Python and TypeScript
from extracted endpoint definitions (from jadx_api_extractor.py, HAR files, or Reqable captures).

Outputs:
  - Python: Async & Sync clients using `httpx` + `pydantic` v2 models
  - TypeScript: Modular typed client using native `fetch` with TypeScript interfaces
  - Quickstart README.md with usage documentation

Conforms to PROJECT.md Interface Contracts.
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple


def sanitize_identifier(name: str) -> str:
    """Converts an arbitrary string into a valid programming identifier."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if not cleaned:
        cleaned = "item"
    if cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def to_snake_case(method: str, path: str) -> str:
    """Generates an idiomatic Python snake_case method name from HTTP method and path."""
    clean_path = re.sub(r'\{[A-Za-z0-9_]+\}', '', path)
    parts = [p for p in clean_path.strip('/').split('/') if p]
    
    # Remove common API prefixes from method name
    filtered_parts = []
    for p in parts:
        if p.lower() in ('api', 'v1', 'v2', 'v3', 'v4', 'rest', 'mobile'):
            continue
        filtered_parts.append(p)
    
    if not filtered_parts:
        filtered_parts = parts or ["root"]

    name_parts = [method.lower()] + [sanitize_identifier(p).lower() for p in filtered_parts]
    return "_".join(name_parts)


def to_camel_case(method: str, path: str) -> str:
    """Generates an idiomatic TypeScript camelCase method name from HTTP method and path."""
    snake = to_snake_case(method, path)
    parts = snake.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def parse_input_spec(data: Any, fallback_base_url: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Normalizes various input formats (jadx output, array of endpoints, or HAR)
    into a standardized endpoint list.
    """
    base_url = fallback_base_url
    endpoints: List[Dict[str, Any]] = []

    if isinstance(data, dict):
        if "base_urls" in data and data["base_urls"]:
            base_url = data["base_urls"][0]
        if "endpoints" in data and isinstance(data["endpoints"], list):
            endpoints = data["endpoints"]
        elif "log" in data and "entries" in data["log"]:  # HAR format
            seen = set()
            for entry in data["log"]["entries"]:
                req = entry.get("request", {})
                url = req.get("url", "")
                method = req.get("method", "GET").upper()
                if not url or url.startswith("data:"):
                    continue
                # Extract path
                match = re.match(r'(https?://[^/]+)(/.*)?', url)
                if match:
                    base_url = match.group(1)
                    path = match.group(2) or "/"
                    # Strip query string
                    path_clean = path.split('?')[0]
                    key = (method, path_clean)
                    if key not in seen:
                        seen.add(key)
                        endpoints.append({
                            "method": method,
                            "path": path_clean,
                            "base_url": base_url,
                            "full_url": url,
                            "headers": {h["name"]: h["value"] for h in req.get("headers", []) if h["name"].lower() not in ('host', 'content-length', 'connection')},
                            "query_params": [q["name"] for q in req.get("queryString", [])],
                            "path_params": [],
                            "body_type": None
                        })
    elif isinstance(data, list):
        endpoints = data

    # Normalize endpoints
    clean_endpoints = []
    for ep in endpoints:
        m = ep.get("method", "GET").upper()
        p = ep.get("path", "/")
        if not p.startswith("/"):
            p = "/" + p

        # Extract path params from template if missing
        path_params = ep.get("path_params", [])
        if not path_params:
            path_params = re.findall(r'\{([a-zA-Z0-9_]+)\}', p)

        clean_endpoints.append({
            "method": m,
            "path": p,
            "base_url": ep.get("base_url") or base_url,
            "headers": ep.get("headers", {}),
            "query_params": ep.get("query_params", []),
            "path_params": path_params,
            "body_type": ep.get("body_type")
        })

    return base_url, clean_endpoints


def generate_python_sdk(client_name: str, base_url: str, endpoints: List[Dict[str, Any]]) -> str:
    """Generates a complete, typed, async and sync Python SDK using httpx and pydantic."""
    lines = [
        '"""',
        f'Auto-generated API Client SDK: {client_name}',
        'Built with httpx and pydantic v2.',
        '"""',
        '',
        'import json',
        'from typing import Any, Dict, List, Optional, Union',
        'import httpx',
        'from pydantic import BaseModel, Field',
        '',
        '',
        'class ApiError(Exception):',
        '    """Raised when an API request fails with a non-2xx status code."""',
        '    def __init__(self, status_code: int, message: str, payload: Any = None):',
        '        super().__init__(f"API Error {status_code}: {message}")',
        '        self.status_code = status_code',
        '        self.message = message',
        '        self.payload = payload',
        '',
        '',
        'class BaseClientConfig(BaseModel):',
        f'    base_url: str = "{base_url}"',
        '    auth_token: Optional[str] = None',
        '    api_key: Optional[str] = None',
        '    timeout: float = 30.0',
        '    headers: Dict[str, str] = Field(default_factory=dict)',
        '',
        ''
    ]

    # Generate Pydantic models for endpoints with bodies
    models_generated = set()
    for ep in endpoints:
        b_type = ep.get("body_type")
        if b_type and b_type not in ('String', 'Object', 'Any') and b_type not in models_generated:
            models_generated.add(b_type)
            clean_model = sanitize_identifier(b_type)
            lines.extend([
                f'class {clean_model}(BaseModel):',
                '    """Request payload model."""',
                '    # TODO: Define specific fields extracted from static analysis',
                '    payload: Dict[str, Any] = Field(default_factory=dict)',
                '',
                ''
            ])

    # Async Client Class
    lines.extend([
        f'class {client_name}:',
        '    """Asynchronous API Client."""',
        '',
        '    def __init__(',
        '        self,',
        f'        base_url: str = "{base_url}",',
        '        auth_token: Optional[str] = None,',
        '        api_key: Optional[str] = None,',
        '        timeout: float = 30.0,',
        '        custom_headers: Optional[Dict[str, str]] = None,',
        '        http_client: Optional[httpx.AsyncClient] = None',
        '    ):',
        '        self.base_url = base_url.rstrip("/")',
        '        self.auth_token = auth_token',
        '        self.api_key = api_key',
        '        self.timeout = timeout',
        '        self.custom_headers = custom_headers or {}',
        '        self._client = http_client or httpx.AsyncClient(timeout=timeout)',
        '        self._managed_client = http_client is None',
        '',
        '    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:',
        '        h = {',
        '            "User-Agent": "ReverseEngineeredClient/1.0",',
        '            "Accept": "application/json",',
        '        }',
        '        if self.auth_token:',
        '            h["Authorization"] = f"Bearer {self.auth_token}"',
        '        if self.api_key:',
        '            h["X-API-Key"] = self.api_key',
        '        h.update(self.custom_headers)',
        '        if extra_headers:',
        '            h.update(extra_headers)',
        '        return h',
        '',
        '    async def close(self):',
        '        """Closes the underlying HTTP client."""',
        '        if self._managed_client and not self._client.is_closed:',
        '            await self._client.aclose()',
        '',
        '    async def __aenter__(self):',
        '        return self',
        '',
        '    async def __aexit__(self, exc_type, exc_val, exc_tb):',
        '        await self.close()',
        ''
    ])

    # Generate async methods
    seen_methods = set()
    for ep in endpoints:
        method = ep["method"]
        path = ep["path"]
        method_name = to_snake_case(method, path)
        if method_name in seen_methods:
            method_name = f"{method_name}_{len(seen_methods)}"
        seen_methods.add(method_name)

        path_params = ep.get("path_params", [])
        query_params = ep.get("query_params", [])
        body_type = ep.get("body_type")

        # Parameter list
        param_list = ["self"]
        for pp in path_params:
            param_list.append(f"{sanitize_identifier(pp)}: Union[str, int]")
        if query_params:
            for qp in query_params:
                param_list.append(f"{sanitize_identifier(qp)}: Optional[Union[str, int, bool]] = None")
        if method in ("POST", "PUT", "PATCH"):
            param_list.append("body: Optional[Union[Dict[str, Any], BaseModel, str]] = None")
        param_list.append("headers: Optional[Dict[str, str]] = None")

        params_signature = ", ".join(param_list)

        # Path interpolation
        formatted_path = path
        for pp in path_params:
            formatted_path = formatted_path.replace(f"{{{pp}}}", f"{{{sanitize_identifier(pp)}}}")

        lines.extend([
            f'    async def {method_name}({params_signature}) -> Any:',
            f'        """{method} {path}"""',
            f'        url = f"{{self.base_url}}{formatted_path}"',
            '        req_headers = self._get_headers(headers)',
        ])

        if query_params:
            lines.append('        params = {')
            for qp in query_params:
                clean_qp = sanitize_identifier(qp)
                lines.append(f'            "{qp}": {clean_qp},')
            lines.append('        }')
            lines.append('        # Filter out None values')
            lines.append('        params = {k: v for k, v in params.items() if v is not None}')
        else:
            lines.append('        params = None')

        lines.extend([
            '        req_kwargs: Dict[str, Any] = {"headers": req_headers, "params": params}',
        ])

        if method in ("POST", "PUT", "PATCH"):
            lines.extend([
                '        if body is not None:',
                '            if isinstance(body, BaseModel):',
                '                req_kwargs["json"] = body.model_dump()',
                '            elif isinstance(body, dict):',
                '                req_kwargs["json"] = body',
                '            else:',
                '                req_kwargs["content"] = str(body)',
            ])

        lines.extend([
            f'        resp = await self._client.request("{method}", url, **req_kwargs)',
            '        if resp.is_error:',
            '            try:',
            '                payload = resp.json()',
            '            except Exception:',
            '                payload = resp.text',
            '            raise ApiError(resp.status_code, resp.reason_phrase, payload)',
            '        try:',
            '            return resp.json()',
            '        except Exception:',
            '            return resp.text',
            ''
        ])

    # Sync Client Class
    sync_name = f"Sync{client_name}"
    lines.extend([
        f'class {sync_name}:',
        '    """Synchronous API Client."""',
        '',
        '    def __init__(',
        '        self,',
        f'        base_url: str = "{base_url}",',
        '        auth_token: Optional[str] = None,',
        '        api_key: Optional[str] = None,',
        '        timeout: float = 30.0,',
        '        custom_headers: Optional[Dict[str, str]] = None',
        '    ):',
        '        self.base_url = base_url.rstrip("/")',
        '        self.auth_token = auth_token',
        '        self.api_key = api_key',
        '        self.timeout = timeout',
        '        self.custom_headers = custom_headers or {}',
        '        self._client = httpx.Client(timeout=timeout)',
        '',
        '    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:',
        '        h = {',
        '            "User-Agent": "ReverseEngineeredClient/1.0",',
        '            "Accept": "application/json",',
        '        }',
        '        if self.auth_token:',
        '            h["Authorization"] = f"Bearer {self.auth_token}"',
        '        if self.api_key:',
        '            h["X-API-Key"] = self.api_key',
        '        h.update(self.custom_headers)',
        '        if extra_headers:',
        '            h.update(extra_headers)',
        '        return h',
        '',
        '    def close(self):',
        '        self._client.close()',
        '',
        '    def __enter__(self):',
        '        return self',
        '',
        '    def __exit__(self, exc_type, exc_val, exc_tb):',
        '        self.close()',
        ''
    ])

    # Generate sync methods
    seen_methods_sync = set()
    for ep in endpoints:
        method = ep["method"]
        path = ep["path"]
        method_name = to_snake_case(method, path)
        if method_name in seen_methods_sync:
            method_name = f"{method_name}_{len(seen_methods_sync)}"
        seen_methods_sync.add(method_name)

        path_params = ep.get("path_params", [])
        query_params = ep.get("query_params", [])

        param_list = ["self"]
        for pp in path_params:
            param_list.append(f"{sanitize_identifier(pp)}: Union[str, int]")
        if query_params:
            for qp in query_params:
                param_list.append(f"{sanitize_identifier(qp)}: Optional[Union[str, int, bool]] = None")
        if method in ("POST", "PUT", "PATCH"):
            param_list.append("body: Optional[Union[Dict[str, Any], BaseModel, str]] = None")
        param_list.append("headers: Optional[Dict[str, str]] = None")

        params_signature = ", ".join(param_list)

        formatted_path = path
        for pp in path_params:
            formatted_path = formatted_path.replace(f"{{{pp}}}", f"{{{sanitize_identifier(pp)}}}")

        lines.extend([
            f'    def {method_name}({params_signature}) -> Any:',
            f'        """{method} {path}"""',
            f'        url = f"{{self.base_url}}{formatted_path}"',
            '        req_headers = self._get_headers(headers)',
        ])

        if query_params:
            lines.append('        params = {')
            for qp in query_params:
                clean_qp = sanitize_identifier(qp)
                lines.append(f'            "{qp}": {clean_qp},')
            lines.append('        }')
            lines.append('        params = {k: v for k, v in params.items() if v is not None}')
        else:
            lines.append('        params = None')

        lines.extend([
            '        req_kwargs: Dict[str, Any] = {"headers": req_headers, "params": params}',
        ])

        if method in ("POST", "PUT", "PATCH"):
            lines.extend([
                '        if body is not None:',
                '            if isinstance(body, BaseModel):',
                '                req_kwargs["json"] = body.model_dump()',
                '            elif isinstance(body, dict):',
                '                req_kwargs["json"] = body',
                '            else:',
                '                req_kwargs["content"] = str(body)',
            ])

        lines.extend([
            f'        resp = self._client.request("{method}", url, **req_kwargs)',
            '        if resp.is_error:',
            '            try:',
            '                payload = resp.json()',
            '            except Exception:',
            '                payload = resp.text',
            '            raise ApiError(resp.status_code, resp.reason_phrase, payload)',
            '        try:',
            '            return resp.json()',
            '        except Exception:',
            '            return resp.text',
            ''
        ])

    return "\n".join(lines)


def generate_typescript_sdk(client_name: str, base_url: str, endpoints: List[Dict[str, Any]]) -> str:
    """Generates a complete, typed TypeScript SDK using native fetch."""
    lines = [
        '/**',
        f' * Auto-generated TypeScript API Client: {client_name}',
        ' * Uses native fetch and strict TypeScript interfaces.',
        ' */',
        '',
        'export interface ClientConfig {',
        '    baseUrl?: string;',
        '    authToken?: string;',
        '    apiKey?: string;',
        '    headers?: Record<string, string>;',
        '}',
        '',
        'export class ApiError extends Error {',
        '    public statusCode: number;',
        '    public payload: any;',
        '',
        '    constructor(statusCode: number, message: string, payload?: any) {',
        '        super(`API Error ${statusCode}: ${message}`);',
        '        this.name = "ApiError";',
        '        this.statusCode = statusCode;',
        '        this.payload = payload;',
        '    }',
        '}',
        ''
    ]

    # Generate TypeScript Client Class
    lines.extend([
        f'export class {client_name} {{',
        '    private baseUrl: string;',
        '    private authToken?: string;',
        '    private apiKey?: string;',
        '    private defaultHeaders: Record<string, string>;',
        '',
        '    constructor(config: ClientConfig = {}) {',
        f'        this.baseUrl = (config.baseUrl || "{base_url}").replace(/\\/+$/, "");',
        '        this.authToken = config.authToken;',
        '        this.apiKey = config.apiKey;',
        '        this.defaultHeaders = config.headers || {};',
        '    }',
        '',
        '    private buildHeaders(extra?: Record<string, string>): Record<string, string> {',
        '        const headers: Record<string, string> = {',
        '            "Accept": "application/json",',
        '            ...this.defaultHeaders,',
        '            ...extra,',
        '        };',
        '        if (this.authToken) {',
        '            headers["Authorization"] = `Bearer ${this.authToken}`;',
        '        }',
        '        if (this.apiKey) {',
        '            headers["X-API-Key"] = this.apiKey;',
        '        }',
        '        return headers;',
        '    }',
        ''
    ])

    seen_methods = set()
    for ep in endpoints:
        method = ep["method"]
        path = ep["path"]
        method_name = to_camel_case(method, path)
        if method_name in seen_methods:
            method_name = f"{method_name}_{len(seen_methods)}"
        seen_methods.add(method_name)

        path_params = ep.get("path_params", [])
        query_params = ep.get("query_params", [])

        # Method signature
        param_list = []
        for pp in path_params:
            param_list.append(f"{sanitize_identifier(pp)}: string | number")
        if query_params:
            qp_type = "{ " + "; ".join(f"{sanitize_identifier(q)}?: string | number | boolean" for q in query_params) + " }"
            param_list.append(f"query?: {qp_type}")
        if method in ("POST", "PUT", "PATCH"):
            param_list.append("body?: any")
        param_list.append("headers?: Record<string, string>")

        signature = ", ".join(param_list)

        # Path replacement for JS template literal
        js_path = path
        for pp in path_params:
            js_path = js_path.replace(f"{{{pp}}}", f"${{{sanitize_identifier(pp)}}}")

        lines.extend([
            f'    async {method_name}({signature}): Promise<any> {{',
            f'        let url = `${{this.baseUrl}}{js_path}`;',
        ])

        if query_params:
            lines.extend([
                '        if (query) {',
                '            const searchParams = new URLSearchParams();',
                '            for (const [key, val] of Object.entries(query)) {',
                '                if (val !== undefined && val !== null) {',
                '                    searchParams.append(key, String(val));',
                '                }',
                '            }',
                '            const qs = searchParams.toString();',
                '            if (qs) {',
                '                url += `?${qs}`;',
                '            }',
                '        }',
            ])

        lines.extend([
            '        const reqHeaders = this.buildHeaders(headers);',
            '        const init: RequestInit = {',
            f'            method: "{method}",',
            '            headers: reqHeaders,',
            '        };',
        ])

        if method in ("POST", "PUT", "PATCH"):
            lines.extend([
                '        if (body !== undefined) {',
                '            if (typeof body === "object" && !(body instanceof FormData)) {',
                '                reqHeaders["Content-Type"] = "application/json";',
                '                init.body = JSON.stringify(body);',
                '            } else {',
                '                init.body = body;',
                '            }',
                '        }',
            ])

        lines.extend([
            '        const response = await fetch(url, init);',
            '        if (!response.ok) {',
            '            let errorPayload: any;',
            '            try {',
            '                errorPayload = await response.json();',
            '            } catch {',
            '                errorPayload = await response.text();',
            '            }',
            '            throw new ApiError(response.status, response.statusText, errorPayload);',
            '        }',
            '        try {',
            '            return await response.json();',
            '        } catch {',
            '            return await response.text();',
            '        }',
            '    }',
            ''
        ])

    lines.append('}\n')
    return "\n".join(lines)


def generate_readme(client_name: str, base_url: str, endpoints: List[Dict[str, Any]]) -> str:
    """Generates user-facing quickstart README."""
    sample_ep = endpoints[0] if endpoints else {"method": "GET", "path": "/api/v1/ping"}
    snake_sample = to_snake_case(sample_ep["method"], sample_ep["path"])
    camel_sample = to_camel_case(sample_ep["method"], sample_ep["path"])

    return f"""# {client_name} - Reconstructed API Client SDK

Auto-generated production-ready client libraries for reverse-engineered endpoints.

- **Base URL**: `{base_url}`
- **Discovered Endpoints**: {len(endpoints)}

---

## Python Quickstart

Requirements: `httpx>=0.24.0`, `pydantic>=2.0.0`

```bash
pip install httpx pydantic
```

### Async Usage:
```python
import asyncio
from client import {client_name}

async def main():
    async with {client_name}(auth_token="YOUR_TOKEN") as client:
        result = await client.{snake_sample}()
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Synchronous Usage:
```python
from client import Sync{client_name}

with Sync{client_name}(auth_token="YOUR_TOKEN") as client:
    result = client.{snake_sample}()
    print(result)
```

---

## TypeScript Quickstart

Works in Node.js (18+), Bun, Deno, and modern browsers without external dependencies.

```typescript
import {{ {client_name} }} from "./client";

async function run() {{
    const client = new {client_name}({{
        authToken: "YOUR_TOKEN"
    }});

    const data = await client.{camel_sample}();
    console.log(data);
}}

run();
```
"""


def main():
    parser = argparse.ArgumentParser(
        description="api_client_generator - Scaffold typed Python & TypeScript API Client SDKs."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to extracted API endpoints JSON (from jadx_api_extractor.py, HAR file, or custom spec)."
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./generated_client",
        help="Directory to save generated SDK code (default: ./generated_client)."
    )
    parser.add_argument(
        "--language", "-l",
        choices=["python", "typescript", "both"],
        default="both",
        help="Target language for generated SDK (default: both)."
    )
    parser.add_argument(
        "--client-name",
        default="ApiClient",
        help="Name of client class (default: ApiClient)."
    )
    parser.add_argument(
        "--base-url",
        default="https://api.example.com",
        help="Fallback base URL if missing in spec."
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"[-] Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"[-] Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    base_url, endpoints = parse_input_spec(raw_data, args.base_url)
    print(f"[*] Loaded {len(endpoints)} endpoint definitions. Primary Base URL: {base_url}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.language in ("python", "both"):
        py_dir = out_dir / "python"
        py_dir.mkdir(parents=True, exist_ok=True)
        py_code = generate_python_sdk(args.client_name, base_url, endpoints)
        py_file = py_dir / "client.py"
        py_file.write_text(py_code, encoding="utf-8")
        # Also create __init__.py
        (py_dir / "__init__.py").write_text(f'from .client import {args.client_name}, Sync{args.client_name}, ApiError\n', encoding="utf-8")
        print(f"[+] Python SDK written to: {py_file}")

    if args.language in ("typescript", "both"):
        ts_dir = out_dir / "typescript"
        ts_dir.mkdir(parents=True, exist_ok=True)
        ts_code = generate_typescript_sdk(args.client_name, base_url, endpoints)
        ts_file = ts_dir / "client.ts"
        ts_file.write_text(ts_code, encoding="utf-8")
        (ts_dir / "index.ts").write_text(f'export * from "./client";\n', encoding="utf-8")
        print(f"[+] TypeScript SDK written to: {ts_file}")

    readme_content = generate_readme(args.client_name, base_url, endpoints)
    (out_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"[+] Quickstart documentation written to: {out_dir / 'README.md'}")
    print("[+] Client generation complete!")


if __name__ == "__main__":
    main()
