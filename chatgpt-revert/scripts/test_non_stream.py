import json
import urllib.request
import urllib.error
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_KEY = "change-me-to-a-long-random-string"
URL = "http://localhost:3000/v1/chat/completions"

payload = {
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": "1 + 1 bằng mấy? Chỉ trả về 1 số duy nhất."}
    ],
    "stream": False
}

req = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    },
    method="POST",
)

print("--- SENDING NON-STREAMING REQUEST ---")
try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print("\nSUCCESS! RESULT:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print("\nHTTPError:", e.code, e.read().decode())
except Exception as e:
    print("\nError:", e)
