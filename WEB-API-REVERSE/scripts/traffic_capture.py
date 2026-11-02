#!/usr/bin/env python3
"""
Traffic Capture — Automated Live Traffic Recorder and Exporter for Reqable MITM Proxy

Interacts with Reqable's local REST API (default: 127.0.0.1:9000) or processes live
capture buffers. Supports domain filtering, status code filtering, static asset
omission, and exports a standardized JSON dataset compatible with downstream
analyzers (`api_analyzer.py`, `har_to_openapi.py`, `curl_to_client.py`).

Standard Output Schema:
[
  {
    "id": str,
    "method": str,
    "url": str,
    "request_headers": dict,
    "request_body": str or None,
    "status_code": int,
    "response_headers": dict,
    "response_body": str or None
  }
]
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


STATIC_EXTENSIONS = {
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".webp", ".avif",
}


def call_reqable_api(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, host: str = "127.0.0.1", port: int = 9000, token: Optional[str] = None) -> Dict[str, Any]:
    """Call Reqable local management REST API."""
    url = f"http://{host}:{port}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    
    auth_token = token or os.environ.get("REQABLE_TOKEN") or "re5q5W9DxzSJiJdVk1tE9hAgWDicvJFPyVOVPWBNJgi3gYX04fDTGVNCPMaZht3LRV"
    if auth_token:
        req.add_header("Authorization", f"Bearer {auth_token}")

    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=encoded_data, timeout=8) as resp:
            body = resp.read().decode("utf-8")
            if body:
                return json.loads(body)
            return {"success": True}
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Reqable API connection error ({url}): {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def normalize_headers(headers: Any) -> Dict[str, str]:
    """Normalize headers list or dict into standard {key: val} dict."""
    res = {}
    if isinstance(headers, list):
        for h in headers:
            if isinstance(h, dict) and "name" in h:
                res[h["name"]] = str(h.get("value", ""))
            elif isinstance(h, (list, tuple)) and len(h) >= 2:
                res[str(h[0])] = str(h[1])
    elif isinstance(headers, dict):
        for k, v in headers.items():
            res[str(k)] = str(v)
    return res


def extract_standard_transaction(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a raw Reqable or HAR traffic item into the standard interface schema."""
    # Check if entry is HAR format
    if "request" in entry and "response" in entry:
        req = entry["request"]
        res = entry["response"]
        url = req.get("url", "")
        method = req.get("method", "GET")
        req_headers = normalize_headers(req.get("headers", []))
        req_body = req.get("postData", {}).get("text")
        status_code = res.get("status", 200)
        res_headers = normalize_headers(res.get("headers", []))
        res_body = res.get("content", {}).get("text")
        item_id = str(entry.get("id") or entry.get("_id") or hash(f"{method}:{url}"))
        return {
            "id": item_id,
            "method": method,
            "url": url,
            "request_headers": req_headers,
            "request_body": req_body,
            "status_code": status_code,
            "response_headers": res_headers,
            "response_body": res_body,
        }

    # Direct Reqable Live Capture format
    url = entry.get("url") or entry.get("path") or ""
    if not url.startswith("http"):
        scheme = entry.get("scheme", "https")
        host = entry.get("host", "localhost")
        url = f"{scheme}://{host}{url}"

    method = entry.get("method", "GET")
    req_headers = normalize_headers(entry.get("request_headers") or entry.get("headers") or [])
    req_body = entry.get("request_body") or entry.get("body")
    status_code = entry.get("status_code") or entry.get("code") or 200
    res_headers = normalize_headers(entry.get("response_headers") or [])
    res_body = entry.get("response_body")
    item_id = str(entry.get("id") or hash(f"{method}:{url}"))

    return {
        "id": item_id,
        "method": method,
        "url": url,
        "request_headers": req_headers,
        "request_body": req_body,
        "status_code": status_code,
        "response_headers": res_headers,
        "response_body": res_body,
    }


def is_static_asset(url: str) -> bool:
    """Check if URL points to a static media or style asset."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in STATIC_EXTENSIONS)


def capture_traffic_session(
    host: str = "127.0.0.1",
    port: int = 9000,
    domain: Optional[str] = None,
    duration: int = 15,
    exclude_static: bool = True,
    status_filter: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Run an automated live capture recording window via Reqable API.
    Enables live capture, polls transactions, and formats the dataset.
    """
    # 1. Enable capture
    enable_res = call_reqable_api("/capture/live/on", method="POST", host=host, port=port)
    if not enable_res.get("success", False) and "error" in enable_res:
        print(f"[!] Warning: Reqable live capture on returned: {enable_res.get('error')}", file=sys.stderr)

    print(f"[*] Recording traffic via Reqable on {host}:{port} for {duration} seconds...", file=sys.stderr)
    start_time = time.time()
    collected: Dict[str, Dict[str, Any]] = {}

    while time.time() - start_time < duration:
        # Build Reqable live filter payload
        filters = []
        if domain:
            filters.append({"type": "host", "hosts": [domain]})
        
        filter_payload = {"filters": filters}
        res = call_reqable_api("/capture/live/filter", method="POST", data=filter_payload, host=host, port=port)
        
        # Reqable returns list of numeric IDs: [11721, 11722, ...]
        record_ids = res if isinstance(res, list) else res.get("data", [])
        
        for r_id in record_ids[-50:]:  # Inspect most recent 50
            s_id = str(r_id)
            if s_id in collected:
                continue
            
            # Fetch record details
            rec = call_reqable_api("/capture/live/get", method="POST", data={"id": r_id}, host=host, port=port)
            if not rec or "url" not in rec:
                continue
            
            # Convert Reqable record to standard format
            req_data = rec.get("request", {})
            res_data = rec.get("response", {}) or {}
            
            url = rec.get("url", "")
            method = req_data.get("method", "GET")
            status_code = res_data.get("code", 0)
            
            if exclude_static and is_static_asset(url):
                continue
            if status_filter and status_code not in status_filter:
                continue
            
            tx = {
                "id": s_id,
                "method": method,
                "url": url,
                "request_headers": normalize_headers(req_data.get("headers", [])),
                "request_body": req_data.get("body"),
                "status_code": status_code,
                "response_headers": normalize_headers(res_data.get("headers", [])),
                "response_body": res_data.get("body", {}).get("text") if isinstance(res_data.get("body"), dict) else None
            }
            collected[s_id] = tx
            print(f"  [+] Captured [{method}] {url[:80]} -> {status_code}", file=sys.stderr)
        
        time.sleep(1.0)

    print(f"[*] Capture complete. Collected {len(collected)} unique HTTP transactions.", file=sys.stderr)
    return list(collected.values())


def parse_existing_traffic_file(file_path: str, domain: Optional[str] = None, exclude_static: bool = True) -> List[Dict[str, Any]]:
    """Parse an existing HAR or JSON traffic capture file and convert to standard schema."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        if "log" in data and "entries" in data["log"]:
            entries = data["log"]["entries"]
        elif "items" in data:
            entries = data["items"]
        elif "data" in data and isinstance(data["data"], list):
            entries = data["data"]
        else:
            entries = [data]

    standardized = []
    for entry in entries:
        tx = extract_standard_transaction(entry)
        if not tx:
            continue
        if domain and domain.lower() not in tx["url"].lower():
            continue
        if exclude_static and is_static_asset(tx["url"]):
            continue
        standardized.append(tx)

    return standardized


def main():
    parser = argparse.ArgumentParser(description="Reqable Live Traffic Capture & Transaction Exporter")
    parser.add_argument("--host", default="127.0.0.1", help="Reqable proxy/API host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9000, help="Reqable proxy/API port (default: 9000)")
    parser.add_argument("--domain", help="Target domain filter (e.g. api.example.com)")
    parser.add_argument("--duration", type=int, default=15, help="Capture recording duration in seconds (default: 15)")
    parser.add_argument("--output", "-o", default="captured_traffic.json", help="Path to write standardized JSON output")
    parser.add_argument("--input-file", help="Parse an existing HAR/JSON capture file instead of live recording")
    parser.add_argument("--status", type=str, help="Comma-separated status codes to include (e.g. 200,201,401)")
    parser.add_argument("--include-static", action="store_true", help="Include static assets (CSS, images, fonts)")

    args = parser.parse_args()
    exclude_static = not args.include_static

    status_filter = None
    if args.status:
        try:
            status_filter = [int(s.strip()) for s in args.status.split(",") if s.strip()]
        except ValueError:
            pass

    if args.input_file:
        if not os.path.exists(args.input_file):
            print(f"[-] Input file not found: {args.input_file}", file=sys.stderr)
            sys.exit(1)
        results = parse_existing_traffic_file(args.input_file, domain=args.domain, exclude_static=exclude_static)
    else:
        results = capture_traffic_session(
            host=args.host,
            port=args.port,
            domain=args.domain,
            duration=args.duration,
            exclude_static=exclude_static,
            status_filter=status_filter,
        )

    # Write output to file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully exported {len(results)} transactions to '{args.output}'")


if __name__ == "__main__":
    main()
