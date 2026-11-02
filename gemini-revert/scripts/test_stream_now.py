import json
import urllib.request
import urllib.error
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URL = "http://localhost:3001/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer change-me-to-a-long-random-string",
}

payload = {
    "model": "gemini-web",
    "messages": [
        {"role": "user", "content": "1 + 1 bằng mấy? Trả lời ngắn gọn 1 từ."}
    ],
    "stream": True
}

print("[*] Sending test request to port 3001...")
req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"), headers=HEADERS, method="POST")

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print("[*] Stream connected! Reading tokens:")
        for line in resp:
            l = line.decode("utf-8").strip()
            if l.startswith("data: "):
                raw = l[6:].strip()
                if raw == "[DONE]":
                    print("\n[*] Stream [DONE] reached.")
                    break
                try:
                    data = json.loads(raw)
                    chunk = data["choices"][0]["delta"].get("content", "")
                    if chunk:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                except Exception as e:
                    pass
except Exception as e:
    print("\n[-] Error:", e)
