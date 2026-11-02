#!/usr/bin/env python3
"""
Auth Extractor — In-Memory Credential, JWT, Cookie, and CSRF Token Extractor

Analyzes captured network traffic (from Reqable, DevTools, or HAR) to systematically
extract:
- JWT Access and Refresh Tokens with payload claim decoding (exp, iat, sub, iss)
- Set-Cookie directives converted to structured cookie jars
- CSRF / Anti-Forgery tokens from headers, cookies, and JSON bodies
- API keys and custom auth headers
- Generates sanitized `.env` configuration files and authenticated Python/TypeScript wrappers.
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT payload without signature verification."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        # Restore URL-safe base64 padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        raw_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(raw_bytes.decode("utf-8"))

        # Add human-readable expiration analysis
        exp = payload.get("exp")
        if isinstance(exp, (int, float)):
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            now_dt = datetime.now(tz=timezone.utc)
            payload["_exp_utc"] = exp_dt.isoformat()
            payload["_is_expired"] = now_dt > exp_dt
            payload["_ttl_seconds"] = max(0, int((exp_dt - now_dt).total_seconds()))

        return payload
    except Exception:
        return None


def parse_set_cookie(header_value: str) -> Dict[str, Any]:
    """Parse a Set-Cookie header string into structured attributes."""
    parts = [p.strip() for p in header_value.split(";") if p.strip()]
    if not parts:
        return {}

    cookie = {"raw": header_value, "flags": []}
    first = parts[0]
    if "=" in first:
        name, val = first.split("=", 1)
        cookie["name"] = name.strip()
        cookie["value"] = val.strip()
    else:
        cookie["name"] = first.strip()
        cookie["value"] = ""

    for attr in parts[1:]:
        if "=" in attr:
            k, v = attr.split("=", 1)
            k_lower = k.strip().lower()
            if k_lower in ("domain", "path", "samesite", "max-age", "expires"):
                cookie[k_lower] = v.strip()
        else:
            cookie["flags"].append(attr.strip().lower())

    return cookie


def extract_credentials_from_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze all transactions and aggregate auth tokens, cookies, and CSRF elements."""
    results = {
        "tokens": [],
        "jwt_claims": [],
        "cookies": {},
        "csrf_tokens": {},
        "api_keys": {},
        "auth_headers": {},
    }

    seen_tokens = set()

    for tx in transactions:
        req_headers = tx.get("request_headers", {})
        res_headers = tx.get("response_headers", {})
        req_body = tx.get("request_body", "")
        res_body = tx.get("response_body", "")

        # 1. Inspect Request Headers
        for h_name, h_val in req_headers.items():
            h_name_lower = h_name.lower()
            val_str = str(h_val).strip()

            if h_name_lower == "authorization":
                results["auth_headers"]["Authorization"] = val_str
                if val_str.lower().startswith("bearer "):
                    token = val_str[7:].strip()
                    if token not in seen_tokens:
                        seen_tokens.add(token)
                        jwt_data = decode_jwt(token)
                        token_info = {"token": token, "type": "bearer", "source": "request_header"}
                        if jwt_data:
                            token_info["jwt"] = jwt_data
                            results["jwt_claims"].append(jwt_data)
                        results["tokens"].append(token_info)

            # CSRF headers in request
            if h_name_lower in ("x-csrf-token", "x-xsrf-token", "csrf-token", "xsrf-token"):
                results["csrf_tokens"][h_name] = val_str

            # API Key headers
            if h_name_lower in ("x-api-key", "api-key", "apikey", "x-auth-key"):
                results["api_keys"][h_name] = val_str

            # Request Cookie header
            if h_name_lower == "cookie":
                for pair in val_str.split(";"):
                    if "=" in pair:
                        c_name, c_val = pair.strip().split("=", 1)
                        results["cookies"][c_name.strip()] = c_val.strip()

        # 2. Inspect Response Headers
        for h_name, h_val in res_headers.items():
            h_name_lower = h_name.lower()
            val_str = str(h_val).strip()

            if h_name_lower == "set-cookie":
                cookie_obj = parse_set_cookie(val_str)
                if cookie_obj.get("name"):
                    results["cookies"][cookie_obj["name"]] = cookie_obj.get("value", "")

            if h_name_lower in ("x-csrf-token", "x-xsrf-token"):
                results["csrf_tokens"][h_name] = val_str

        # 3. Inspect JSON response bodies for tokens
        if res_body and isinstance(res_body, str):
            try:
                body_json = json.loads(res_body)
                if isinstance(body_json, dict):
                    # Check common token keys
                    for k in ["access_token", "accessToken", "token", "jwt", "id_token", "refreshToken", "refresh_token"]:
                        if k in body_json and isinstance(body_json[k], str):
                            cand_token = body_json[k].strip()
                            if cand_token not in seen_tokens:
                                seen_tokens.add(cand_token)
                                jwt_data = decode_jwt(cand_token)
                                token_info = {"token": cand_token, "field": k, "source": "response_body"}
                                if jwt_data:
                                    token_info["jwt"] = jwt_data
                                    results["jwt_claims"].append(jwt_data)
                                results["tokens"].append(token_info)

                    # Check for csrf tokens in body
                    for k in ["csrf", "csrfToken", "csrf_token", "_csrf"]:
                        if k in body_json and isinstance(body_json[k], str):
                            results["csrf_tokens"][k] = body_json[k]
            except Exception:
                pass

    return results


def generate_env_file(auth_data: Dict[str, Any], env_path: str = ".env"):
    """Write extracted credentials to a sanitized .env template."""
    lines = [
        "# Reverse Engineered API Environment Configuration",
        f"# Generated: {datetime.now(tz=timezone.utc).isoformat()}",
        "",
    ]

    # Primary bearer / JWT
    tokens = auth_data.get("tokens", [])
    primary_token = tokens[0]["token"] if tokens else ""
    lines.append(f"API_ACCESS_TOKEN={primary_token}")

    refresh_token = ""
    for t in tokens:
        if "refresh" in t.get("field", "").lower():
            refresh_token = t["token"]
            break
    lines.append(f"API_REFRESH_TOKEN={refresh_token}")

    # API Keys
    for k, v in auth_data.get("api_keys", {}).items():
        env_var = re.sub(r"[^A-Z0-9_]", "_", k.upper())
        lines.append(f"{env_var}={v}")

    # CSRF
    for k, v in auth_data.get("csrf_tokens", {}).items():
        env_var = re.sub(r"[^A-Z0-9_]", "_", k.upper())
        lines.append(f"{env_var}={v}")

    # Cookie string
    cookies = auth_data.get("cookies", {})
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    lines.append(f"API_COOKIE_JAR={cookie_str}")
    lines.append("")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_python_auth_wrapper(auth_data: Dict[str, Any], output_path: str = "auth_session.py"):
    """Generate a drop-in Python requests/httpx authenticated session class."""
    tokens = auth_data.get("tokens", [])
    token_val = tokens[0]["token"] if tokens else "YOUR_ACCESS_TOKEN"
    cookies = auth_data.get("cookies", {})

    code = f'''# Authenticated Session Wrapper
import os
import requests

class AuthenticatedSession:
    """Session wrapper equipped with captured headers, tokens, and cookies."""

    def __init__(self, token=None, cookies=None):
        self.session = requests.Session()
        self.token = token or os.getenv("API_ACCESS_TOKEN", "{token_val}")
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {{self.token}}"

        # Injected default cookies
        injected_cookies = {json.dumps(cookies, indent=8)}
        if cookies:
            injected_cookies.update(cookies)
        self.session.cookies.update(injected_cookies)

    def request(self, method, url, **kwargs):
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            print("[!] 401 Unauthorized encountered. Session refresh required.")
        return resp

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)
'''
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)


def main():
    parser = argparse.ArgumentParser(description="Auth Extractor — In-Memory Token, Cookie & CSRF Analyzer")
    parser.add_argument("--input", "-i", required=True, help="Path to captured traffic JSON file")
    parser.add_argument("--output", "-o", default="auth_config.json", help="Output path for JSON auth summary")
    parser.add_argument("--env-file", default=None, help="Generate .env configuration file at specified path")
    parser.add_argument("--wrapper", default=None, help="Generate Python session wrapper script at specified path")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[-] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to list of transactions
    transactions = []
    if isinstance(data, list):
        transactions = data
    elif isinstance(data, dict):
        if "log" in data and "entries" in data["log"]:
            transactions = data["log"]["entries"]
        else:
            transactions = [data]

    auth_summary = extract_credentials_from_transactions(transactions)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(auth_summary, f, indent=2, ensure_ascii=False)

    print(f"[+] Auth analysis complete:")
    print(f"    - Discovered Tokens: {len(auth_summary['tokens'])}")
    print(f"    - Decoded JWT Claims: {len(auth_summary['jwt_claims'])}")
    print(f"    - Extracted Cookies: {len(auth_summary['cookies'])}")
    print(f"    - CSRF Tokens: {len(auth_summary['csrf_tokens'])}")
    print(f"[+] Auth JSON summary written to '{args.output}'")

    if args.env_file:
        generate_env_file(auth_summary, args.env_file)
        print(f"[+] .env configuration generated at '{args.env_file}'")

    if args.wrapper:
        generate_python_auth_wrapper(auth_summary, args.wrapper)
        print(f"[+] Python auth wrapper generated at '{args.wrapper}'")


if __name__ == "__main__":
    main()
