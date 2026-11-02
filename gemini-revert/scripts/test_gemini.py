import json
import urllib.request
import urllib.error
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_KEY = "change-me-to-a-long-random-string"
URL = "http://localhost:3001/v1/chat/completions"

payload = {
    "model": "gemini-2.5-flash",
    "messages": [
        {"role": "user", "content": "Xin chao Gemini! Tra loi ngan gon 1 cau."}
    ],
    "stream": True
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

print("--- SENDING GEMINI COMPLETION REQUEST ---")
try:
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                raw_data = line_str[6:]
                if raw_data == "[DONE]":
                    print("\n[STREAM COMPLETE]")
                    break
                try:
                    chunk = json.loads(raw_data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                except Exception:
                    pass
except urllib.error.HTTPError as e:
    print("\nHTTPError:", e.code, e.read().decode())
except Exception as e:
    print("\nError:", e)
