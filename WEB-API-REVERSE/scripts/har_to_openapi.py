#!/usr/bin/env python3
"""
HAR to OpenAPI 3.0 Converter

Converts HTTP Archive (HAR) files or captured network traffic into
OpenAPI 3.0 specification (YAML or JSON).

Features:
- Auto-detects path parameters (numeric IDs, UUIDs, MongoDB ObjectIds)
- Infers request/response schemas from JSON bodies
- Groups endpoints by resource/tag
- Supports bearer auth, API key, and cookie-based auth
"""

import json
import sys
import argparse
import re
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from typing import Any, Optional


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert captured network traffic (HAR) to OpenAPI 3.0 spec"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to HAR or captured traffic JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        default="openapi.yaml",
        help="Output file path (default: openapi.yaml)"
    )
    parser.add_argument(
        "--title",
        default="Reverse Engineered API",
        help="API title for the spec"
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="API version (default: 1.0.0)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    parser.add_argument(
        "--filter-domain",
        help="Only include requests to this domain"
    )
    return parser.parse_args()


# Same patterns as api_analyzer for consistency
ID_PATTERNS = [
    (re.compile(r"/(\d+)(?=/|$)"), "/{id}"),
    (re.compile(r"/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I), "/{uuid}"),
    (re.compile(r"/([0-9a-f]{24})(?=/|$)"), "/{objectId}"),
]

STATIC_EXTENSIONS = {
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".webp",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def is_api_request(url: str, content_type: str = "", resource_type: str = "") -> bool:
    """Check if this looks like an API request."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for ext in STATIC_EXTENSIONS:
        if path.endswith(ext):
            return False
    
    if "application/json" in content_type:
        return True
    if any(p in path for p in ["/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/v3/"]):
        return True
    if resource_type.lower() in ("xhr", "fetch"):
        return True
    
    return False


def normalize_path_openapi(path: str) -> tuple:
    """Replace dynamic segments with OpenAPI path parameters. Returns (path, params)."""
    params = []
    normalized = path
    
    for pattern, replacement in ID_PATTERNS:
        match = pattern.search(normalized)
        while match:
            param_name = replacement.strip("/{}")
            # Make param names unique if multiple
            if any(p["name"] == param_name for p in params):
                param_name = f"{param_name}_{len(params)}"
                replacement_unique = "/{" + param_name + "}"
            else:
                replacement_unique = replacement
            
            params.append({
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "example": match.group(1) if match.lastindex else match.group(0).strip("/"),
            })
            normalized = normalized[:match.start()] + replacement_unique + normalized[match.end():]
            match = pattern.search(normalized)
    
    return normalized, params


def infer_json_schema(data: Any, max_depth: int = 4, depth: int = 0) -> dict:
    """Infer JSON Schema from data sample."""
    if depth >= max_depth:
        return {}
    
    if data is None:
        return {"type": "string", "nullable": True}
    if isinstance(data, bool):
        return {"type": "boolean"}
    if isinstance(data, int):
        return {"type": "integer"}
    if isinstance(data, float):
        return {"type": "number"}
    if isinstance(data, str):
        schema = {"type": "string"}
        if re.match(r"^\d{4}-\d{2}-\d{2}T", data):
            schema["format"] = "date-time"
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            schema["format"] = "date"
        elif re.match(r"^https?://", data):
            schema["format"] = "uri"
        elif re.match(r"^[^@]+@[^@]+\.[^@]+$", data):
            schema["format"] = "email"
        elif re.match(r"^[0-9a-f]{8}-", data, re.I):
            schema["format"] = "uuid"
        return schema
    if isinstance(data, list):
        schema = {"type": "array"}
        if data:
            schema["items"] = infer_json_schema(data[0], max_depth, depth + 1)
        else:
            schema["items"] = {}
        return schema
    if isinstance(data, dict):
        properties = {}
        required = []
        for key, value in data.items():
            properties[key] = infer_json_schema(value, max_depth, depth + 1)
            if value is not None:
                required.append(key)
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema
    
    return {}


def extract_headers_dict(headers: Any) -> dict:
    """Normalize headers to dict."""
    if isinstance(headers, list):
        return {h.get("name", ""): h.get("value", "") for h in headers}
    if isinstance(headers, dict):
        return headers
    return {}


def detect_security_schemes(all_headers: list) -> dict:
    """Detect security schemes from collected headers."""
    schemes = {}
    
    for headers in all_headers:
        auth = headers.get("Authorization", headers.get("authorization", ""))
        if auth:
            if auth.startswith("Bearer "):
                schemes["bearerAuth"] = {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT" if auth.count(".") == 2 else "token",
                }
            elif auth.startswith("Basic "):
                schemes["basicAuth"] = {
                    "type": "http",
                    "scheme": "basic",
                }
        
        for key in ["X-API-Key", "X-Api-Key", "x-api-key"]:
            if key in headers:
                schemes["apiKeyAuth"] = {
                    "type": "apiKey",
                    "in": "header",
                    "name": key,
                }
    
    return schemes


def build_openapi_spec(entries: list, title: str, version: str, filter_domain: str = None) -> dict:
    """Build OpenAPI 3.0 spec from network entries."""
    
    paths = defaultdict(dict)
    all_headers = []
    servers = set()
    tags = set()
    
    for entry in entries:
        # Handle both HAR and flat format
        if "request" in entry and isinstance(entry["request"], dict):
            request = entry["request"]
            response = entry.get("response", {})
            url = request.get("url", "")
            method = request.get("method", "GET").lower()
            req_headers = extract_headers_dict(request.get("headers", []))
            resp_headers = extract_headers_dict(response.get("headers", []))
            req_body_raw = request.get("postData", {}).get("text", "")
            resp_body_raw = response.get("content", {}).get("text", "")
            status = response.get("status", 200)
            query_params_raw = request.get("queryString", [])
        else:
            url = entry.get("url", "")
            method = entry.get("method", "GET").lower()
            req_headers = extract_headers_dict(entry.get("request_headers", entry.get("headers", {})))
            resp_headers = extract_headers_dict(entry.get("response_headers", entry.get("responseHeaders", {})))
            req_body_raw = entry.get("request_body", entry.get("postData", entry.get("requestBody", "")))
            resp_body_raw = entry.get("response_body", entry.get("responseBody", entry.get("response", {}).get("body", "")))
            status = entry.get("status_code", entry.get("status", entry.get("response", {}).get("status", 200)))
            query_params_raw = []
        
        if not url or method not in HTTP_METHODS:
            continue
        
        # Get content type
        resp_ct = resp_headers.get("content-type", resp_headers.get("Content-Type", ""))
        resource_type = entry.get("_resourceType", entry.get("type", ""))
        
        if not is_api_request(url, resp_ct, resource_type):
            continue
        
        parsed = urlparse(url)
        
        if filter_domain and parsed.netloc != filter_domain:
            continue
        
        base = f"{parsed.scheme}://{parsed.netloc}"
        servers.add(base)
        all_headers.append(req_headers)
        
        # Normalize path
        path, path_params = normalize_path_openapi(parsed.path)
        
        # Tag from first meaningful path segment
        segments = [s for s in path.split("/") if s and not s.startswith("{")]
        tag = segments[-1] if segments else "default"
        # Skip 'api', 'v1', etc. as tags
        skip_tags = {"api", "v1", "v2", "v3", "rest", "graphql"}
        for seg in segments:
            if seg.lower() not in skip_tags:
                tag = seg
                break
        tags.add(tag)
        
        # Build operation
        operation = {
            "tags": [tag],
            "summary": f"{method.upper()} {path}",
            "operationId": f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}",
        }
        
        # Path parameters
        if path_params:
            operation["parameters"] = path_params
        
        # Query parameters
        query_dict = parse_qs(parsed.query)
        if isinstance(query_params_raw, list) and query_params_raw:
            for qp in query_params_raw:
                name = qp.get("name", "")
                if name and "parameters" not in operation:
                    operation["parameters"] = []
                if name:
                    param = {
                        "name": name,
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    }
                    if qp.get("value"):
                        param["example"] = qp["value"]
                    # Avoid duplicates
                    if not any(p.get("name") == name and p.get("in") == "query"
                              for p in operation.get("parameters", [])):
                        operation.setdefault("parameters", []).append(param)
        elif query_dict:
            for name, values in query_dict.items():
                param = {
                    "name": name,
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                }
                if values:
                    param["example"] = values[0]
                operation.setdefault("parameters", []).append(param)
        
        # Request body
        if method in ("post", "put", "patch") and req_body_raw:
            try:
                body_data = json.loads(req_body_raw) if isinstance(req_body_raw, str) else req_body_raw
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": infer_json_schema(body_data),
                        }
                    }
                }
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Response
        status_str = str(status)
        responses = {}
        if resp_body_raw:
            try:
                resp_data = json.loads(resp_body_raw) if isinstance(resp_body_raw, str) else resp_body_raw
                responses[status_str] = {
                    "description": f"Status {status}",
                    "content": {
                        "application/json": {
                            "schema": infer_json_schema(resp_data),
                        }
                    }
                }
            except (json.JSONDecodeError, TypeError):
                responses[status_str] = {"description": f"Status {status}"}
        else:
            responses[status_str] = {"description": f"Status {status}"}
        
        operation["responses"] = responses
        
        # Merge into paths (don't overwrite existing operations)
        if method not in paths[path]:
            paths[path][method] = operation
    
    # Build security schemes
    security_schemes = detect_security_schemes(all_headers)
    
    # Assemble spec
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": f"API specification reverse-engineered from network traffic. {len(paths)} endpoints discovered.",
        },
        "servers": [{"url": s} for s in sorted(servers)],
        "paths": dict(paths),
    }
    
    if security_schemes:
        spec["components"] = {"securitySchemes": security_schemes}
        spec["security"] = [{name: [] for name in security_schemes}]
    
    if tags:
        spec["tags"] = [{"name": t} for t in sorted(tags)]
    
    return spec


def write_yaml(spec: dict, output_path: str):
    """Write spec as YAML. Falls back to JSON if PyYAML not available."""
    try:
        import yaml
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"[+] OpenAPI spec (YAML) written to: {output_path}")
    except ImportError:
        # Fallback to JSON if yaml not installed
        json_path = output_path.replace(".yaml", ".json").replace(".yml", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"[!] PyYAML not installed, wrote JSON instead: {json_path}")
        print(f"    Install PyYAML: pip install pyyaml")


def main():
    args = parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle HAR format
    if "log" in data and "entries" in data["log"]:
        entries = data["log"]["entries"]
    elif isinstance(data, list):
        entries = data
    elif "entries" in data:
        entries = data["entries"]
    else:
        print("[!] Unrecognized format. Expected HAR or array of entries.")
        sys.exit(1)
    
    print(f"[*] Loaded {len(entries)} network entries")
    
    spec = build_openapi_spec(entries, args.title, args.version, args.filter_domain)
    path_count = len(spec.get("paths", {}))
    print(f"[*] Generated OpenAPI spec with {path_count} paths")
    
    if args.format == "yaml":
        write_yaml(spec, args.output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"[+] OpenAPI spec (JSON) written to: {args.output}")


if __name__ == "__main__":
    main()
