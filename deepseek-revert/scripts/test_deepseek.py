import json
import sys
import time
import urllib.request

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

URL = "http://localhost:3002/v1/chat/completions"
API_KEY = "sk-deepseek-local-key"

payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "user", "content": "1 + 1 bằng mấy? Trả lời thật ngắn."}
    ],
    "stream": True
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print(f"[*] Sending streaming test request to {URL}...")
t0 = time.time()
req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data: "):
                continue
            raw = line_str[6:].strip()
            if raw == "[DONE]":
                print("\n\n[DONE] Stream finished cleanly.")
                break
            try:
                data = json.loads(raw)
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    print(delta, end="", flush=True)
            except Exception as e:
                print(f"[Parse Error: {e}]", flush=True)
    print(f"\nElapsed time: {time.time() - t0:.2f}s")
except Exception as e:
    print(f"\nRequest Error: {e}")
