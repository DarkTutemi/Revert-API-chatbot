import json
import urllib.request

# Start profile 12a7e7b1-30e5-4665-85e2-0f9cce81f060 (61577091256835)
profile_id = "12a7e7b1-30e5-4665-85e2-0f9cce81f060"
url = f"http://127.0.0.1:9495/api/v3/profiles/start/{profile_id}"

req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("GPM Start response:", data)
except Exception as e:
    print("Error starting GPM profile:", e)
