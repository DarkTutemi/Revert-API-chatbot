#!/usr/bin/env python3
"""
GPM Reqable Launcher — Anti-Detect Browser Automation Routed via Reqable MITM Proxy

Automates creation, configuration, launch, and teardown of GPM Login anti-detection
browser profiles routed through Reqable (127.0.0.1:9000). Provides fallback to
native Chrome with proxy flags when GPM Login Local API is unavailable.

Outputs profile metadata including remote debugging port and WebSocket URL
for direct CDP attachment by Chrome DevTools MCP or automation frameworks.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


DEFAULT_GPM_PORT = 9495
DEFAULT_REQABLE_PROXY = "http://127.0.0.1:9000"


def find_gpm_port() -> int:
    """
    Determine GPM Local API port:
    1. Checks environment variable GPM_PORT
    2. Checks standard fallback file `http.port` in local app data
    3. Defaults to 9495
    """
    env_port = os.getenv("GPM_PORT")
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass

    # Check AppData paths for http.port
    app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if app_data:
        possible_paths = [
            os.path.join(app_data, "GPMLogin", "http.port"),
            os.path.join(app_data, "GpmLogin", "http.port"),
            os.path.join(app_data, "gpm", "http.port"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        val = f.read().strip()
                        if val.isdigit():
                            return int(val)
                except Exception:
                    pass

    return DEFAULT_GPM_PORT


def call_gpm_api(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, port: int = DEFAULT_GPM_PORT) -> Dict[str, Any]:
    """Call GPM Login Local API endpoint."""
    url = f"http://127.0.0.1:{port}/api/v1{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=encoded_data, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.URLError as e:
        return {"success": False, "message": f"Connection error to GPM API on port {port}: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


def list_profiles(search: Optional[str] = None, port: int = DEFAULT_GPM_PORT) -> list:
    """Retrieve list of profiles matching search query."""
    params = {}
    if search:
        params["search"] = search
    query_str = f"?{urllib.parse.urlencode(params)}" if params else ""
    res = call_gpm_api(f"/profiles{query_str}", method="GET", port=port)
    if res.get("success"):
        data = res.get("data", {})
        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
    return []


def create_stealth_profile(name: str, proxy: str = DEFAULT_REQABLE_PROXY, port: int = DEFAULT_GPM_PORT) -> Optional[str]:
    """
    Creates an anti-detection profile with noise injected into
    Canvas, WebGL, Audio, ClientRects, and Fonts, routed through Reqable proxy.
    """
    payload = {
        "name": name,
        "raw_proxy": proxy,
        "browser_type": 1,  # 1 = Chrome
        "os_type": 1,        # 1 = Windows
        "canvas_mode": 1,    # Noise
        "webgl_image_mode": 1,     # Noise
        "webgl_metadata_mode": 1,  # Emulated
        "audio_mode": 1,     # Noise
        "client_rect_mode": 1,  # Noise
        "font_mode": 1,      # Emulated
        "webrtc_mode": 1,    # Replace with proxy IP
        "note": "Created via api-reverse-engineer automation",
    }
    res = call_gpm_api("/profiles/create", method="POST", data=payload, port=port)
    if res.get("success"):
        data = res.get("data", {})
        if isinstance(data, dict):
            return data.get("id") or data.get("profile_id")
        elif isinstance(data, str):
            return data
    return None


def start_profile(profile_id: str, port: int = DEFAULT_GPM_PORT) -> Dict[str, Any]:
    """Launch the GPM browser profile and return CDP endpoint."""
    res = call_gpm_api(f"/profiles/start/{profile_id}?skip_proxy_check=true", method="GET", port=port)
    return res


def stop_profile(profile_id: str, port: int = DEFAULT_GPM_PORT) -> Dict[str, Any]:
    """Gracefully terminate a running GPM browser profile."""
    res = call_gpm_api(f"/profiles/stop/{profile_id}", method="GET", port=port)
    return res


def launch_fallback_chrome(proxy: str, remote_port: int = 9222) -> Optional[subprocess.Popen]:
    """
    Fallback mechanism when GPM Login is not active:
    Launches system Google Chrome with remote debugging and proxy routing.
    """
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    target_chrome = None
    for p in chrome_paths:
        if os.path.exists(p):
            target_chrome = p
            break

    if not target_chrome:
        return None

    # Parse proxy address
    proxy_server = proxy.replace("http://", "").replace("https://", "")
    temp_profile_dir = os.path.join(os.getenv("TEMP", r"C:\Temp"), f"chrome_re_proxy_{remote_port}")

    cmd = [
        target_chrome,
        f"--remote-debugging-port={remote_port}",
        f"--proxy-server={proxy_server}",
        f"--user-data-dir={temp_profile_dir}",
        "--ignore-certificate-errors",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="GPM Login Stealth Browser Launcher with Reqable Proxy Routing")
    parser.add_argument("--name", default="Reqable_Reversing_Profile", help="Profile name to find or create")
    parser.add_argument("--proxy", default=DEFAULT_REQABLE_PROXY, help="Reqable proxy URL (e.g. http://127.0.0.1:9000)")
    parser.add_argument("--port", type=int, default=0, help="GPM Local API port (0 = auto-detect)")
    parser.add_argument("--start", action="store_true", help="Start the profile and return CDP endpoint")
    parser.add_argument("--stop", action="store_true", help="Stop the profile")
    parser.add_argument("--id", help="Explicit profile UUID for start/stop")
    parser.add_argument("--fallback-chrome", action="store_true", default=True, help="Fallback to Chrome if GPM API is offline")

    args = parser.parse_args()
    gpm_port = args.port if args.port > 0 else find_gpm_port()

    # Handle Stop action
    if args.stop:
        target_id = args.id
        if not target_id:
            # Look up by name
            profiles = list_profiles(search=args.name, port=gpm_port)
            if profiles:
                target_id = profiles[0].get("id")
        if not target_id:
            print(json.dumps({"success": False, "message": "Profile ID or name not found"}))
            sys.exit(1)
        res = stop_profile(target_id, port=gpm_port)
        print(json.dumps(res, indent=2))
        return

    # Handle Start action (default if --start given or implicitly when run)
    target_id = args.id
    if not target_id:
        existing = list_profiles(search=args.name, port=gpm_port)
        for p in existing:
            if p.get("name") == args.name:
                target_id = p.get("id")
                break

        if not target_id:
            # Create stealth profile
            target_id = create_stealth_profile(args.name, proxy=args.proxy, port=gpm_port)

    if target_id:
        launch_res = start_profile(target_id, port=gpm_port)
        if launch_res.get("success"):
            data = launch_res.get("data", {})
            result = {
                "success": True,
                "engine": "gpm_login",
                "profile_id": target_id,
                "remote_debugging_port": data.get("remote_debugging_port"),
                "websocket_debugging_url": data.get("websocket_debugging_url"),
                "proxy": args.proxy,
                "message": "GPM stealth profile started and routed through Reqable proxy.",
            }
            print(json.dumps(result, indent=2))
            return
        else:
            msg = launch_res.get("message", "Failed to start GPM profile")
    else:
        msg = f"GPM API unreachable on port {gpm_port}"

    # Fallback path if requested
    if args.fallback_chrome:
        proc = launch_fallback_chrome(proxy=args.proxy, remote_port=9222)
        if proc:
            result = {
                "success": True,
                "engine": "fallback_chrome",
                "remote_debugging_port": 9222,
                "websocket_debugging_url": "ws://127.0.0.1:9222/devtools/browser",
                "proxy": args.proxy,
                "message": f"GPM unavailable ({msg}). Launched fallback Chrome routed through Reqable.",
            }
            print(json.dumps(result, indent=2))
            return

    print(json.dumps({"success": False, "message": msg}, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()
