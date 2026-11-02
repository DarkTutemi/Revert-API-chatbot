import curl_cffi.requests
import json
import uuid
import sys

sys.stdout.reconfigure(encoding='utf-8')

access_token = """eyJhbGciOiJSUzI1NiIsImtpZCI6IlNsdFlQZ2haN1I1UkFHZzM0em00eF9fc0FrVzAyd2VXT0t6SFlCc2tZNkUiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJhbXIiOlsidXJuOm9wZW5haTphbXI6Z29vZ2xlIl0sImNoYXRncHRfbG9naW5fZmluYWxpemVyX2F1dGhfc2Vzc2lvbl9pZCI6ImF1dGhzZXNzX01TT1A3SFFYQ0IwbUlpa2xwQ1dQNVNhYyIsImNoYXRncHRfbG9naW5fZmluYWxpemVyX2ludml0ZV9pbnRlbnRfYm91bmQiOnRydWUsInVzZXJfaWQiOiJ1c2VyLWJhMXFlTDVMVEZZU0xGazRKb2tkTWRveCIsImNoYXRncHRfYWNjb3VudF91c2VyX2lkIjoidXNlci1iYTFxZUw1TFRGWVNMRms0Sm9rZE1kb3hfXzgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfYWNjb3VudF9pZCI6IjgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItYmExcWVMNUxURllTTEZrNEpva2RNZG94IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJmcmVlIiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X2NvbXB1dGVfcmVzaWRlbmN5Ijoibm9fY29uc3RyYWludCJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJtZC5ob3NzYW4wNTdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZhbWlseV9uYW1lIjoiTWQuaG9zc2FuIiwiZ2l2ZW5fbmFtZSI6Ik1kLmhvc3NhbiIsIm5hbWUiOiJNZC5ob3NzYW4gTWQuaG9zc2FuIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0pEQnN6YkJ5NHkyYzA0TVUwYi1ZMEhjQ2ZRZGt3ODhWUkdnUTlxbkhRSEZiLUJHcFU9czk2LWMifSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJwd2RfYXV0aF90aW1lIjoxNzkzNTIzMjE3NTkyLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJwcm9maWxlIiwib2ZmbGluZV9hY2Nlc3MiLCJtb2RlbC5yZXF1ZXN0IiwibW9kZWwucmVhZCIsIm9yZ2FuaXphdGlvbi5yZWFkIiwib3JnYW5pemF0aW9uLndyaXRlIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NU09QN0hRWENCMG1JaWtscENXUDVTYWMiLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDIwNDU2NTk0ODIzMzE1NDYzMTEiLCJpYXQiOjE3OTM1MjMyMTksImV4cCI6MTc5NDM4NzIxOCwianRpIjoiMzI1OWM2M2E3ODEyNGI0YmFlNTRhOTkwYjkwMWJmMGMiLCJuYmYiOjE3OTM1MjMyMTl9.tZa4Kgm_dxEvKBpaE1fowbFaPqdi7Sw5TzW5KsS8IlMRFxlJh8SX5bKKnWD_Yez99I9flXe84aHu_SPHc_EhJvJ0b-OHnDwRgh0jq5oGdHAndHbCOaESPOK29Tmyw7V7B3CQgXFXem-MGEoGEE0tx-USsNyQHKfxbpAqhE3eOeuVkWDTRANxYoOyNeoTSfbH-lZoGgh2D4wVsRGHgPPr8aUTaO1qljTccNM5sNLPoFghkZ2lY-T0qmet71YaWLhmr3fTSIv_HpTLp-RMBD1HOngZPrchRq06cqfZtODgPyEWVHyqu5tIKM9RxUcclvO3Q41pgfCWKpTRZAQJI_0YeQ""".strip()

s = curl_cffi.requests.Session(impersonate="chrome124")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Authorization": f"Bearer {access_token}",
    "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
    "origin": "https://chatgpt.com",
    "referer": "https://chatgpt.com/",
    "content-type": "application/json",
    "oai-device-id": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "oai-did": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "oai-language": "vi-VN",
}

# 1. Fetch requirements
r_req = s.post("https://chatgpt.com/backend-api/sentinel/chat-requirements", headers=headers, json={})
req_data = r_req.json()
print("Requirements response:", req_data.get("persona"))
chat_token = req_data.get("token")
if chat_token:
    headers["openai-sentinel-chat-requirements-token"] = chat_token

# 2. Test call to /backend-api/f/conversation
payload = {
    "turn_attribution": {"turn_trigger": "composer"},
    "action": "next",
    "model": "auto",
    "parent_message_id": str(uuid.uuid4()),
    "timezone": "Asia/Saigon",
    "timezone_offset_min": -420,
    "is_do_not_remember": False,
    "client_contextual_info": {
        "app_name": "chatgpt.com",
        "app_surface": "codex_browser",
        "has_web_push_capabilities": True,
        "web_push_notification_permission": "default",
    },
    "local_function_names": ["local.continue_in_work"],
    "messages": [
        {
            "author": {"metadata": {}, "name": None, "role": "user"},
            "channel": None,
            "content": {"content_type": "text", "parts": ["hello"]},
            "create_time": 1793524942.205,
            "end_turn": None,
            "id": str(uuid.uuid4()),
            "metadata": {},
            "recipient": "all",
            "status": "finished_successfully",
            "update_time": None,
            "weight": 1,
        }
    ],
    "supported_encodings": ["v1"],
    "genui_state_snapshots": [],
    "client_prepare_state": "success",
}

resp = s.post("https://chatgpt.com/backend-api/f/conversation", headers=headers, json=payload, stream=True, timeout=30)
print("f/conversation status:", resp.status_code)
for line in resp.iter_lines():
    if line:
        txt = line.decode("utf-8", errors="replace")
        print(txt[:120])
        if "data: [DONE]" in txt:
            break
