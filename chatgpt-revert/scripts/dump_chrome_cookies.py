import browser_cookie3
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    cj = browser_cookie3.chrome(domain_name="chatgpt.com")
    cookies = {c.name: c.value for c in cj}
    print("Found cookies:", list(cookies.keys()))
    for k in ["oai-did", "__Secure-next-auth.session-token.0", "__Secure-next-auth.session-token.1", "__cf_bm", "_cfuvid"]:
        if k in cookies:
            print(f"{k}: {cookies[k][:20]}... (len {len(cookies[k])})")
except Exception as e:
    print("Error reading chrome cookies:", e)
