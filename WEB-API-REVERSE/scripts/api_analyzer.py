#!/usr/bin/env python3
"""
API Analyzer — Parse captured network traffic and generate API documentation.

Reads captured network requests (JSON format from DevTools/HAR) and produces:
- Structured API endpoint listing
- Request/response schema analysis
- Auth mechanism detection
- cURL/Python/JS code snippets
"""

import json
import sys
import argparse
import re
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from typing import Any


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze captured network traffic and generate API documentation"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to captured traffic JSON file (HAR or DevTools export)"
    )
    parser.add_argument(
        "--output", "-o",
        default="api_documentation.md",
        help="Output markdown file path (default: api_documentation.md)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--filter-domain",
        help="Only include requests to this domain"
    )
    parser.add_argument(
        "--exclude-static",
        action="store_true",
        default=True,
        help="Exclude static assets (images, CSS, JS, fonts)"
    )
    return parser.parse_args()


STATIC_EXTENSIONS = {
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".webp", ".avif",
}

# Patterns that look like IDs in URL paths
ID_PATTERNS = [
    (re.compile(r"/\d+(?=/|$)"), "/:id"),
    (re.compile(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I), "/:uuid"),
    (re.compile(r"/[0-9a-f]{24}(?=/|$)"), "/:objectId"),
    (re.compile(r"/[A-Za-z0-9_-]{20,}(?=/|$)"), "/:slug"),
]


def is_api_request(entry: dict) -> bool:
    """Filter for actual API requests, not static assets."""
    url = entry.get("url", "") or entry.get("request", {}).get("url", "")
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Skip static assets
    for ext in STATIC_EXTENSIONS:
        if path.endswith(ext):
            return False

    # Include common API patterns
    api_indicators = ["/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/v3/"]
    content_type = ""
    
    # Check response content type
    headers = entry.get("response_headers", entry.get("response", {}).get("headers", []))
    if isinstance(headers, list):
        for h in headers:
            if h.get("name", "").lower() == "content-type":
                content_type = h.get("value", "").lower()
    elif isinstance(headers, dict):
        content_type = headers.get("content-type", headers.get("Content-Type", "")).lower()

    if "application/json" in content_type:
        return True
    
    if any(ind in path for ind in api_indicators):
        return True

    # Check if XHR/fetch
    resource_type = entry.get("_resourceType", entry.get("type", ""))
    if resource_type in ("xhr", "fetch", "XHR", "Fetch"):
        return True

    return False


def normalize_path(path: str) -> str:
    """Replace dynamic path segments with parameter placeholders."""
    normalized = path
    for pattern, replacement in ID_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def extract_headers(headers: Any) -> dict:
    """Normalize headers from different formats to a dict."""
    if isinstance(headers, list):
        return {h["name"]: h["value"] for h in headers if "name" in h}
    if isinstance(headers, dict):
        return headers
    return {}


def detect_auth_mechanism(headers: dict) -> dict:
    """Detect authentication mechanism from request headers."""
    auth_info = {"type": "none", "details": {}}
    
    auth_header = headers.get("Authorization", headers.get("authorization", ""))
    if auth_header:
        if auth_header.startswith("Bearer "):
            auth_info["type"] = "bearer_jwt" if auth_header.count(".") == 2 else "bearer_token"
            auth_info["details"]["token_preview"] = auth_header[:50] + "..."
        elif auth_header.startswith("Basic "):
            auth_info["type"] = "basic"
        elif auth_header.startswith("Digest "):
            auth_info["type"] = "digest"
    
    # Check for API key headers
    for key in ["X-API-Key", "X-Api-Key", "x-api-key", "api-key", "apikey"]:
        if key in headers:
            auth_info["type"] = "api_key"
            auth_info["details"]["header"] = key
            break
    
    # Check cookies for session tokens
    cookies = headers.get("Cookie", headers.get("cookie", ""))
    if cookies:
        session_patterns = ["session", "sid", "token", "auth", "jwt"]
        for pattern in session_patterns:
            if pattern.lower() in cookies.lower():
                if auth_info["type"] == "none":
                    auth_info["type"] = "cookie_session"
                auth_info["details"]["has_session_cookie"] = True
                break
    
    # CSRF tokens
    for key in ["X-CSRF-Token", "X-XSRF-TOKEN", "csrf-token"]:
        if key in headers:
            auth_info["details"]["csrf_header"] = key
    
    return auth_info


def infer_schema(data: Any, max_depth: int = 3, depth: int = 0) -> dict:
    """Infer JSON schema from a data sample."""
    if depth >= max_depth:
        return {"type": "any"}
    
    if data is None:
        return {"type": "null"}
    if isinstance(data, bool):
        return {"type": "boolean"}
    if isinstance(data, int):
        return {"type": "integer"}
    if isinstance(data, float):
        return {"type": "number"}
    if isinstance(data, str):
        # Try to detect specific string formats
        if re.match(r"^\d{4}-\d{2}-\d{2}", data):
            return {"type": "string", "format": "date-time"}
        if re.match(r"^https?://", data):
            return {"type": "string", "format": "uri"}
        if re.match(r"^[^@]+@[^@]+\.[^@]+$", data):
            return {"type": "string", "format": "email"}
        return {"type": "string"}
    if isinstance(data, list):
        if len(data) > 0:
            return {"type": "array", "items": infer_schema(data[0], max_depth, depth + 1)}
        return {"type": "array", "items": {"type": "any"}}
    if isinstance(data, dict):
        properties = {}
        for key, value in data.items():
            properties[key] = infer_schema(value, max_depth, depth + 1)
        return {"type": "object", "properties": properties}
    
    return {"type": "unknown"}


def schema_to_str(schema: dict, indent: int = 0) -> str:
    """Convert inferred schema to a readable string."""
    prefix = "  " * indent
    schema_type = schema.get("type", "unknown")
    fmt = schema.get("format", "")
    
    if schema_type in ("string", "integer", "number", "boolean", "null"):
        return f"{schema_type}" + (f" ({fmt})" if fmt else "")
    
    if schema_type == "array":
        items = schema.get("items", {})
        return f"array<{schema_to_str(items, indent)}>"
    
    if schema_type == "object":
        props = schema.get("properties", {})
        if not props:
            return "object"
        lines = ["object {"]
        for key, val in props.items():
            lines.append(f"{prefix}  {key}: {schema_to_str(val, indent + 1)}")
        lines.append(f"{prefix}" + "}")
        return "\n".join(lines)
    
    return schema_type


def parse_har(data: dict) -> list:
    """Parse HAR format into normalized entries."""
    entries = []
    for entry in data.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        response = entry.get("response", {})
        
        normalized = {
            "url": request.get("url", ""),
            "method": request.get("method", "GET"),
            "request": {
                "headers": request.get("headers", []),
                "body": request.get("postData", {}).get("text", ""),
                "queryString": request.get("queryString", []),
            },
            "response": {
                "status": response.get("status", 0),
                "headers": response.get("headers", []),
                "body": response.get("content", {}).get("text", ""),
                "size": response.get("content", {}).get("size", 0),
            },
            "time": entry.get("time", 0),
        }
        entries.append(normalized)
    return entries


def parse_devtools_export(data: Any) -> list:
    """Parse Chrome DevTools network export format."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "entries" in data:
        return data["entries"]
    if isinstance(data, dict) and "log" in data:
        return parse_har(data)
    return []


def analyze_traffic(entries: list, filter_domain: str = None) -> dict:
    """Analyze network traffic entries and group by endpoint."""
    endpoints = defaultdict(lambda: {
        "methods": set(),
        "urls": [],
        "request_headers": {},
        "response_statuses": set(),
        "query_params": defaultdict(set),
        "request_bodies": [],
        "response_bodies": [],
        "auth": None,
        "count": 0,
    })
    
    for entry in entries:
        if not is_api_request(entry):
            continue
        
        url = entry.get("url", "") or entry.get("request", {}).get("url", "")
        if not url:
            continue
        
        parsed = urlparse(url)
        
        if filter_domain and parsed.netloc != filter_domain:
            continue
        
        method = entry.get("method", "") or entry.get("request", {}).get("method", "GET")
        path = parsed.path
        normalized = normalize_path(path)
        base = f"{parsed.scheme}://{parsed.netloc}"
        endpoint_key = f"{method.upper()} {normalized}"
        
        ep = endpoints[endpoint_key]
        ep["methods"].add(method.upper())
        ep["urls"].append(url)
        ep["base_url"] = base
        ep["path"] = normalized
        ep["count"] += 1
        
        # Parse query params
        qp = parse_qs(parsed.query)
        for key, values in qp.items():
            ep["query_params"][key].update(values)
        
        # Extract headers
        req_headers = extract_headers(
            entry.get("request_headers", entry.get("request", {}).get("headers", entry.get("headers", {})))
        )
        ep["request_headers"].update(req_headers)
        
        # Detect auth
        auth = detect_auth_mechanism(req_headers)
        if auth["type"] != "none":
            ep["auth"] = auth
        
        # Response status
        status = entry.get("status_code", entry.get("response", {}).get("status", 0) or entry.get("status", 0))
        if status:
            ep["response_statuses"].add(status)
        
        # Request body (limit samples)
        req_body = entry.get("request_body", entry.get("request", {}).get("body", "") or entry.get("postData", ""))
        if req_body and len(ep["request_bodies"]) < 3:
            try:
                ep["request_bodies"].append(json.loads(req_body))
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Response body (limit samples)
        resp_body = entry.get("response_body", entry.get("response", {}).get("body", "") or entry.get("responseBody", ""))
        if resp_body and len(ep["response_bodies"]) < 3:
            try:
                ep["response_bodies"].append(json.loads(resp_body))
            except (json.JSONDecodeError, TypeError):
                pass
    
    return dict(endpoints)


def generate_markdown(endpoints: dict, output_path: str):
    """Generate markdown API documentation from analyzed endpoints."""
    lines = [
        "# API Documentation — Reverse Engineered",
        "",
        f"> Auto-generated from captured network traffic ({len(endpoints)} endpoints discovered)",
        "",
        "---",
        "",
    ]
    
    # Group by base resource
    resources = defaultdict(list)
    for key, ep in sorted(endpoints.items()):
        path = ep.get("path", "")
        parts = [p for p in path.split("/") if p and not p.startswith(":")]
        resource = parts[-1] if parts else "root"
        resources[resource].append((key, ep))
    
    # Auth summary
    auth_types = set()
    for key, ep in endpoints.items():
        if ep.get("auth"):
            auth_types.add(ep["auth"]["type"])
    
    if auth_types:
        lines.extend([
            "## Authentication",
            "",
            "| Type | Details |",
            "|------|---------|",
        ])
        for at in auth_types:
            lines.append(f"| `{at}` | Detected in request headers |")
        lines.extend(["", "---", ""])
    
    # Endpoints by resource
    for resource, eps in sorted(resources.items()):
        lines.extend([
            f"## {resource.title().replace('_', ' ')}",
            "",
        ])
        
        for key, ep in eps:
            method = list(ep["methods"])[0] if ep["methods"] else "GET"
            path = ep.get("path", "")
            base = ep.get("base_url", "")
            
            lines.extend([
                f"### `{method} {path}`",
                "",
                f"- **Full URL**: `{base}{path}`",
                f"- **Calls observed**: {ep['count']}",
                f"- **Status codes**: {', '.join(str(s) for s in sorted(ep['response_statuses']))}",
            ])
            
            if ep.get("auth"):
                lines.append(f"- **Auth**: `{ep['auth']['type']}`")
            
            # Query params
            if ep["query_params"]:
                lines.extend(["", "**Query Parameters:**", ""])
                lines.append("| Parameter | Example Values |")
                lines.append("|-----------|---------------|")
                for param, values in sorted(ep["query_params"].items()):
                    examples = ", ".join(list(values)[:3])
                    lines.append(f"| `{param}` | `{examples}` |")
            
            # Request body schema
            if ep["request_bodies"]:
                schema = infer_schema(ep["request_bodies"][0])
                lines.extend([
                    "",
                    "**Request Body:**",
                    "```",
                    schema_to_str(schema),
                    "```",
                ])
            
            # Response body schema
            if ep["response_bodies"]:
                schema = infer_schema(ep["response_bodies"][0])
                lines.extend([
                    "",
                    "**Response Body:**",
                    "```",
                    schema_to_str(schema),
                    "```",
                ])
            
            # cURL example
            lines.extend([
                "",
                "**cURL:**",
                "```bash",
                f'curl -X {method} "{base}{path}"',
                "```",
                "",
                "---",
                "",
            ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"[+] API documentation written to: {output_path}")
    print(f"[+] Total endpoints: {len(endpoints)}")


def generate_json(endpoints: dict, output_path: str):
    """Generate JSON summary of analyzed endpoints."""
    output = []
    for key, ep in sorted(endpoints.items()):
        output.append({
            "endpoint": key,
            "base_url": ep.get("base_url", ""),
            "path": ep.get("path", ""),
            "methods": list(ep["methods"]),
            "statuses": sorted(ep["response_statuses"]),
            "auth": ep.get("auth"),
            "query_params": {k: list(v) for k, v in ep["query_params"].items()},
            "call_count": ep["count"],
            "request_schema": infer_schema(ep["request_bodies"][0]) if ep["request_bodies"] else None,
            "response_schema": infer_schema(ep["response_bodies"][0]) if ep["response_bodies"] else None,
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"[+] JSON output written to: {output_path}")


def main():
    args = parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    entries = parse_devtools_export(data)
    print(f"[*] Loaded {len(entries)} network entries")
    
    endpoints = analyze_traffic(entries, args.filter_domain)
    print(f"[*] Found {len(endpoints)} unique API endpoints")
    
    if args.format == "markdown":
        generate_markdown(endpoints, args.output)
    else:
        generate_json(endpoints, args.output)


if __name__ == "__main__":
    main()
