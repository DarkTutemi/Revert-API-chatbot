import curl_cffi.requests
import json
import uuid
import sys

sys.stdout.reconfigure(encoding='utf-8')

access_token = """eyJhbGciOiJSUzI1NiIsImtpZCI6IlNsdFlQZ2haN1I1UkFHZzM0em00eF9fc0FrVzAyd2VXT0t6SFlCc2tZNkUiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJhbXIiOlsidXJuOm9wZW5haTphbXI6Z29vZ2xlIl0sImNoYXRncHRfbG9naW5fZmluYWxpemVyX2F1dGhfc2Vzc2lvbl9pZCI6ImF1dGhzZXNzX01TT1A3SFFYQ0IwbUlpa2xwQ1dQNVNhYyIsImNoYXRncHRfbG9naW5fZmluYWxpemVyX2ludml0ZV9pbnRlbnRfYm91bmQiOnRydWUsInVzZXJfaWQiOiJ1c2VyLWJhMXFlTDVMVEZZU0xGazRKb2tkTWRveCIsImNoYXRncHRfYWNjb3VudF91c2VyX2lkIjoidXNlci1iYTFxZUw1TFRGWVNMRms0Sm9rZE1kb3hfXzgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfYWNjb3VudF9pZCI6IjgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItYmExcWVMNUxURllTTEZrNEpva2RNZG94IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJmcmVlIiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X2NvbXB1dGVfcmVzaWRlbmN5Ijoibm9fY29uc3RyYWludCJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJtZC5ob3NzYW4wNTdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZhbWlseV9uYW1lIjoiTWQuaG9zc2FuIiwiZ2l2ZW5fbmFtZSI6Ik1kLmhvc3NhbiIsIm5hbWUiOiJNZC5ob3NzYW4gTWQuaG9zc2FuIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0pEQnN6YkJ5NHkyYzA0TVUwYi1ZMEhjQ2ZRZGt3ODhWUkdnUTlxbkhRSEZiLUJHcFU9czk2LWMifSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJwd2RfYXV0aF90aW1lIjoxNzkzNTIzMjE3NTkyLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJwcm9maWxlIiwib2ZmbGluZV9hY2Nlc3MiLCJtb2RlbC5yZXF1ZXN0IiwibW9kZWwucmVhZCIsIm9yZ2FuaXphdGlvbi5yZWFkIiwib3JnYW5pemF0aW9uLndyaXRlIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NU09QN0hRWENCMG1JaWtscENXUDVTYWMiLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDIwNDU2NTk0ODIzMzE1NDYzMTEiLCJpYXQiOjE3OTM1MjMyMTksImV4cCI6MTc5NDM4NzIxOCwianRpIjoiMzI1OWM2M2E3ODEyNGI0YmFlNTRhOTkwYjkwMWJmMGMiLCJuYmYiOjE3OTM1MjMyMTl9.tZa4Kgm_dxEvKBpaE1fowbFaPqdi7Sw5TzW5KsS8IlMRFxlJh8SX5bKKnWD_Yez99I9flXe84aHu_SPHc_EhJvJ0b-OHnDwRgh0jq5oGdHAndHbCOaESPOK29Tmyw7V7B3CQgXFXem-MGEoGEE0tx-USsNyQHKfxbpAqhE3eOeuVkWDTRANxYoOyNeoTSfbH-lZoGgh2D4wVsRGHgPPr8aUTaO1qljTccNM5sNLPoFghkZ2lY-T0qmet71YaWLhmr3fTSIv_HpTLp-RMBD1HOngZPrchRq06cqfZtODgPyEWVHyqu5tIKM9RxUcclvO3Q41pgfCWKpTRZAQJI_0YeQ""".strip()

s = curl_cffi.requests.Session(impersonate="chrome124")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Authorization": f"Bearer {access_token}",
    "originator": "Codex Browser",
    "x-openai-web-frontend": "codex_webview",
    "x-openai-codex-window-type": "browser",
    "x-openai-rate-limit-join-workspace": "1",
    "OAI-Language": "vi-VN",
    "oai-did": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "OAI-Device-Id": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "ChatGPT-Account-Id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
    "Origin": "https://chatgpt.com",
    "Referer": "https://chatgpt.com/",
    "Content-Type": "application/json",
}

# 1. Call conversation/init
r_init = s.post("https://chatgpt.com/backend-api/conversation/init", headers=headers, json={})
print("Init status:", r_init.status_code)
print("Init body:", r_init.text)
