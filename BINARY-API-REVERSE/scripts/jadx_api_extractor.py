#!/usr/bin/env python3
"""
jadx_api_extractor.py

Automated static reverse engineering tool for Android APKs and decompiled source code.
Extracts:
  - Retrofit 2 and OkHttp interfaces, HTTP methods, paths, headers, and params
  - Base URLs and hardcoded API endpoints
  - AndroidManifest.xml deep links, permissions, and network security configs
  - Embedded API keys, JWT tokens, AWS credentials, and secrets in code and resources

Conforms to PROJECT.md Interface Contracts and feeds directly into api_client_generator.py.
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple


# Regex patterns for static API discovery
RETROFIT_METHOD_PATTERN = re.compile(
    r'@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(\s*["\']([^"\']*)["\']\s*\)',
    re.MULTILINE
)
RETROFIT_HEADERS_PATTERN = re.compile(
    r'@Headers\s*\(\s*(?:\{([^}]*)\}|["\']([^"\']*)["\'])\s*\)',
    re.MULTILINE
)
RETROFIT_HEADER_SINGLE_PATTERN = re.compile(
    r'@Header\s*\(\s*["\']([^"\']+)["\']\s*\)\s*(?:@\w+\s*)*([A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)',
    re.MULTILINE
)
RETROFIT_QUERY_PATTERN = re.compile(
    r'@Query\s*\(\s*["\']([^"\']+)["\']\s*\)',
    re.MULTILINE
)
RETROFIT_PATH_PARAM_PATTERN = re.compile(
    r'@Path\s*\(\s*["\']([^"\']+)["\']\s*\)',
    re.MULTILINE
)
RETROFIT_BODY_PATTERN = re.compile(
    r'@Body\s*(?:@\w+\s*)*([A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)',
    re.MULTILINE
)
RETROFIT_FUNCTION_SIGNATURE = re.compile(
    r'(?:public\s+|abstract\s+)*(?:Call<([A-Za-z0-9_<>,\s]+)>|Single<([A-Za-z0-9_<>,\s]+)>|Observable<([A-Za-z0-9_<>,\s]+)>|Flow<([A-Za-z0-9_<>,\s]+)>|suspend\s+fun\s+[A-Za-z0-9_]+\s*\([^)]*\)\s*:\s*([A-Za-z0-9_<>,\s]+)|([A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)\s*\([^)]*\))',
    re.MULTILINE
)

BASE_URL_PATTERNS = [
    re.compile(r'\.baseUrl\s*\(\s*["\'](https?://[^"\']+)["\']\s*\)', re.IGNORECASE),
    re.compile(r'HttpUrl\.parse\s*\(\s*["\'](https?://[^"\']+)["\']\s*\)', re.IGNORECASE),
    re.compile(r'(?:BASE_URL|API_URL|SERVER_URL|API_ENDPOINT|HOST_URL)\s*=\s*["\'](https?://[^"\']+)["\']', re.IGNORECASE),
    re.compile(r'BASE_URL\s*:\s*String\s*=\s*["\'](https?://[^"\']+)["\']', re.IGNORECASE)
]

GENERAL_URL_PATTERN = re.compile(
    r'["\'](https?://[a-zA-Z0-9_\-\.]+(?::[0-9]+)?(?:/[a-zA-Z0-9_\-\.~%!$&\'()*+,;=:@/]*)*(?:\?[a-zA-Z0-9_\-\.~%!$&\'()*+,;=:@/?]*)?)["\']'
)

IGNORED_URL_PREFIXES = (
    'http://schemas.android.com',
    'https://schemas.android.com',
    'http://www.w3.org',
    'https://www.w3.org',
    'http://apache.org',
    'https://apache.org',
    'http://xmlpull.org',
    'http://ns.adobe.com',
    'https://plus.google.com',
    'https://play.google.com/store',
    'https://developer.android.com',
    'https://github.com'
)

SECRET_KEY_PATTERNS = [
    (r'AIza[0-9A-Za-z\-_]{35}', 'Google API Key'),
    (r'ya29\.[0-9A-Za-z\-_]+', 'Google OAuth Access Token'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'(?i)aws.{0,20}?(?:secret|key).{0,5}?["\']([0-9a-zA-Z/+]{40})["\']', 'AWS Secret Key'),
    (r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', 'JSON Web Token (JWT)'),
    (r'xox[baprs]-[0-9a-zA-Z]{10,48}', 'Slack Token'),
    (r'basic\s+[A-Za-z0-9+/=]{20,}', 'Basic Auth Token'),
    (r'(?i)(?:api_key|apikey|app_key|client_secret|auth_token)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{16,64})["\']', 'Generic API Key/Secret')
]


def find_jadx_executable() -> Optional[str]:
    """Locate jadx CLI on the host system."""
    cmd = shutil.which("jadx")
    if cmd:
        return cmd
    cmd_bat = shutil.which("jadx.bat")
    if cmd_bat:
        return cmd_bat
    return None


def run_jadx_decompile(apk_path: str, output_dir: str, extra_args: List[str] = None) -> bool:
    """Decompiles an APK using jadx."""
    jadx_cmd = find_jadx_executable()
    if not jadx_cmd:
        print("[-] Error: 'jadx' command not found in PATH. Please install jadx or decompile first.", file=sys.stderr)
        return False

    cmd = [jadx_cmd, "-d", output_dir]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(apk_path)

    print(f"[*] Running JADX: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[+] JADX decompilation finished successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] JADX decompilation failed: {e.stderr}", file=sys.stderr)
        return False


def parse_manifest(decompiled_dir: Path) -> Dict[str, Any]:
    """Extracts metadata from AndroidManifest.xml."""
    manifest_info = {
        "package": None,
        "version_code": None,
        "version_name": None,
        "network_security_config": None,
        "permissions": [],
        "deep_links": []
    }

    manifest_file = decompiled_dir / "resources" / "AndroidManifest.xml"
    if not manifest_file.exists():
        manifest_file = decompiled_dir / "AndroidManifest.xml"
    
    if not manifest_file.exists():
        return manifest_info

    try:
        content = manifest_file.read_text(encoding="utf-8", errors="ignore")
        
        # Package name
        pkg_m = re.search(r'package\s*=\s*["\']([^"\']+)["\']', content)
        if pkg_m:
            manifest_info["package"] = pkg_m.group(1)

        # Network Security Config
        nsc_m = re.search(r'android:networkSecurityConfig\s*=\s*["\']([^"\']+)["\']', content)
        if nsc_m:
            manifest_info["network_security_config"] = nsc_m.group(1)

        # Permissions
        for perm in re.finditer(r'<uses-permission[^>]+android:name\s*=\s*["\']([^"\']+)["\']', content):
            manifest_info["permissions"].append(perm.group(1))

        # Deep links / Intent filters
        # Search for scheme & host combinations
        schemes = re.findall(r'android:scheme\s*=\s*["\']([^"\']+)["\']', content)
        hosts = re.findall(r'android:host\s*=\s*["\']([^"\']+)["\']', content)
        for s in set(schemes):
            if s not in ('http', 'https', 'android'):
                manifest_info["deep_links"].append(f"{s}://")
        for s in schemes:
            for h in hosts:
                manifest_info["deep_links"].append(f"{s}://{h}")

        manifest_info["deep_links"] = list(set(manifest_info["deep_links"]))
    except Exception as e:
        print(f"[-] Warning parsing AndroidManifest.xml: {e}", file=sys.stderr)

    return manifest_info


def scan_resource_secrets(decompiled_dir: Path) -> List[Dict[str, str]]:
    """Scans XML resource files for embedded API keys and secrets."""
    extracted = []
    res_dir = decompiled_dir / "resources" / "res"
    if not res_dir.exists():
        res_dir = decompiled_dir / "res"
    if not res_dir.exists():
        return extracted

    xml_files = list(res_dir.glob("values*/*.xml"))
    for xf in xml_files:
        try:
            text = xf.read_text(encoding="utf-8", errors="ignore")
            # Look for string resource tags
            for m in re.finditer(r'<string\s+name\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</string>', text, re.DOTALL):
                name, val = m.group(1), m.group(2).strip()
                for pattern, sec_type in SECRET_KEY_PATTERNS:
                    if re.search(pattern, val):
                        extracted.append({
                            "key": val,
                            "type": f"{sec_type} ({name})",
                            "source": str(xf.relative_to(decompiled_dir)).replace("\\", "/")
                        })
                        break
        except Exception:
            pass

    return extracted


def scan_source_code(decompiled_dir: Path) -> Tuple[List[Dict[str, Any]], Set[str], List[Dict[str, str]]]:
    """
    Scans Java and Kotlin source files for Retrofit endpoints, base URLs, and secrets.
    """
    endpoints: List[Dict[str, Any]] = []
    base_urls: Set[str] = set()
    code_secrets: List[Dict[str, str]] = []

    src_dir = decompiled_dir / "sources"
    if not src_dir.exists():
        src_dir = decompiled_dir

    source_files = list(src_dir.glob("**/*.java")) + list(src_dir.glob("**/*.kt"))

    for sf in source_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            rel_path = str(sf.relative_to(decompiled_dir)).replace("\\", "/")
            lines = content.splitlines()

            # 1. Base URLs search
            for b_pat in BASE_URL_PATTERNS:
                for match in b_pat.finditer(content):
                    url = match.group(1).rstrip('/')
                    if not url.startswith(IGNORED_URL_PREFIXES):
                        base_urls.add(url)

            # 2. General URL search
            for match in GENERAL_URL_PATTERN.finditer(content):
                url = match.group(1)
                if not url.startswith(IGNORED_URL_PREFIXES) and "/api" in url:
                    # Potential full endpoint
                    root_part = re.match(r'(https?://[^/]+)', url)
                    if root_part:
                        base_urls.add(root_part.group(1))

            # 3. Secret patterns search
            for pattern, sec_type in SECRET_KEY_PATTERNS:
                for match in re.finditer(pattern, content):
                    key_val = match.group(0)
                    if not any(s["key"] == key_val for s in code_secrets):
                        code_secrets.append({
                            "key": key_val,
                            "type": sec_type,
                            "source": rel_path
                        })

            # 4. Retrofit interface parsing
            # Search for methods with @GET, @POST, etc.
            for match in RETROFIT_METHOD_PATTERN.finditer(content):
                method = match.group(1).upper()
                path = match.group(2)
                match_start = match.start()
                
                # Line number
                line_no = content[:match_start].count('\n') + 1

                # Look forward for method signature (up to 500 characters)
                snippet = content[match_start:match_start + 600]
                
                # Extract headers
                headers = {}
                headers_match = RETROFIT_HEADERS_PATTERN.search(snippet)
                if headers_match:
                    h_block = headers_match.group(1) or headers_match.group(2) or ""
                    for h_line in re.findall(r'["\']([^"\']+)["\']', h_block):
                        if ':' in h_line:
                            k, v = h_line.split(':', 1)
                            headers[k.strip()] = v.strip()

                # Extract single headers in params
                for h_single in RETROFIT_HEADER_SINGLE_PATTERN.finditer(snippet):
                    headers[h_single.group(1)] = f"{{{h_single.group(3)}}}"

                # Extract query parameters
                query_params = [q.group(1) for q in RETROFIT_QUERY_PATTERN.finditer(snippet)]

                # Extract path parameters
                path_params = [p.group(1) for p in RETROFIT_PATH_PARAM_PATTERN.finditer(snippet)]
                # Also extract {param} from path template
                template_params = re.findall(r'\{([A-Za-z0-9_]+)\}', path)
                for tp in template_params:
                    if tp not in path_params:
                        path_params.append(tp)

                # Extract body model type
                body_type = None
                body_match = RETROFIT_BODY_PATTERN.search(snippet)
                if body_match:
                    body_type = body_match.group(1)

                # Extract return type
                return_type = "Object"
                sig_match = RETROFIT_FUNCTION_SIGNATURE.search(snippet)
                if sig_match:
                    for g in sig_match.groups():
                        if g:
                            return_type = g.strip()
                            break

                endpoints.append({
                    "method": method,
                    "path": path,
                    "base_url": "",  # Will be resolved or matched
                    "full_url": path if path.startswith("http") else "",
                    "headers": headers,
                    "query_params": query_params,
                    "path_params": path_params,
                    "body_type": body_type,
                    "return_type": return_type,
                    "source_file": rel_path,
                    "source_line": line_no
                })

        except Exception as e:
            print(f"[-] Error parsing {sf}: {e}", file=sys.stderr)

    return endpoints, base_urls, code_secrets


def resolve_base_urls(endpoints: List[Dict[str, Any]], base_urls: Set[str]) -> List[Dict[str, Any]]:
    """Assigns the best matching base_url to endpoints lacking full URLs."""
    primary_base = list(base_urls)[0] if base_urls else "https://api.example.com"

    for ep in endpoints:
        if not ep["base_url"]:
            ep["base_url"] = primary_base
        if not ep["full_url"]:
            p = ep["path"].lstrip('/')
            ep["full_url"] = f"{ep['base_url']}/{p}"

    return endpoints


def export_markdown(data: Dict[str, Any], output_path: str):
    """Writes extracted API information as a comprehensive Markdown report."""
    md = []
    app_info = data.get("app_info", {})
    md.append(f"# API Reverse Engineering Report: {app_info.get('package', 'Unknown Package')}\n")
    
    md.append("## 1. Application Overview")
    md.append(f"- **Package Name**: `{app_info.get('package')}`")
    md.append(f"- **Network Security Config**: `{app_info.get('network_security_config', 'Default')}`")
    md.append(f"- **Deep Links**: {', '.join(f'`{dl}`' for dl in app_info.get('deep_links', [])) or 'None'}\n")

    md.append("## 2. Discovered Base URLs")
    for b in data.get("base_urls", []):
        md.append(f"- `{b}`")
    md.append("")

    md.append(f"## 3. Discovered Endpoints ({len(data.get('endpoints', []))})")
    md.append("| Method | Path | Return Type | Body Type | Source |")
    md.append("|:---|:---|:---|:---|:---|")
    for ep in data.get("endpoints", []):
        md.append(f"| `{ep['method']}` | `{ep['path']}` | `{ep['return_type']}` | `{ep['body_type'] or '-'}` | `{ep['source_file']}:{ep['source_line']}` |")
    md.append("")

    md.append(f"## 4. Extracted Secrets & API Keys ({len(data.get('extracted_keys', []))})")
    md.append("| Key / Token | Type | Source File |")
    md.append("|:---|:---|:---|")
    for sec in data.get("extracted_keys", []):
        md.append(f"| `{sec['key'][:35]}...` | {sec['type']} | `{sec['source']}` |")
    md.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    parser = argparse.ArgumentParser(
        description="jadx_api_extractor - Static API & Endpoint Extraction from Android APKs and DEX bytecode."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to target .apk file or directory of decompiled source code."
    )
    parser.add_argument(
        "--output", "-o",
        default="extracted_api.json",
        help="Output file path (.json or .md). Defaults to extracted_api.json."
    )
    parser.add_argument(
        "--decompile-dir",
        default="./jadx_decompiled",
        help="Cache directory for JADX decompilation (default: ./jadx_decompiled)."
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown"],
        default="json",
        help="Output format: json or markdown."
    )
    parser.add_argument(
        "--skip-decompile",
        action="store_true",
        help="Skip decompilation if target directory already exists."
    )
    parser.add_argument(
        "--jadx-args",
        nargs="*",
        default=["--threads-count", "8", "--no-res"],
        help="Additional arguments to pass to JADX."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[-] Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    decompiled_dir: Path

    if input_path.is_file() and input_path.suffix.lower() == ".apk":
        decompiled_dir = Path(args.decompile_dir)
        if not (args.skip_decompile and decompiled_dir.exists()):
            print(f"[*] Decompiling APK: {input_path} -> {decompiled_dir}")
            success = run_jadx_decompile(str(input_path), str(decompiled_dir), args.jadx_args)
            if not success:
                print("[-] Aborting due to decompilation failure.", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"[*] Using existing decompiled directory: {decompiled_dir}")
    else:
        decompiled_dir = input_path

    print(f"[*] Analyzing source and resources in: {decompiled_dir}")
    manifest_info = parse_manifest(decompiled_dir)
    resource_secrets = scan_resource_secrets(decompiled_dir)
    endpoints, base_urls, code_secrets = scan_source_code(decompiled_dir)

    all_secrets = resource_secrets + code_secrets
    endpoints = resolve_base_urls(endpoints, base_urls)

    result = {
        "app_info": manifest_info,
        "base_urls": sorted(list(base_urls)),
        "endpoints": endpoints,
        "extracted_keys": all_secrets
    }

    print(f"[+] Discovered {len(endpoints)} API endpoints.")
    print(f"[+] Discovered {len(base_urls)} Base URLs: {list(base_urls)}")
    print(f"[+] Discovered {len(all_secrets)} API keys and secret tokens.")

    output_path = args.output
    if args.format == "markdown" or output_path.endswith(".md"):
        export_markdown(result, output_path)
        print(f"[+] Markdown report written to: {output_path}")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[+] Structured JSON catalogue written to: {output_path}")


if __name__ == "__main__":
    main()
