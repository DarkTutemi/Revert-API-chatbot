# chatgpt-proxy-stack

ChatGPT web → OpenAI-compatible API → MCP tools.

## Stack

- **cf_bypass/** — Cloudflare clearance (curl_cffi + Playwright fallback)
- **auth/** — token lifecycle + multi-account pool
- **api/** — FastAPI gateway, OpenAI-compatible endpoints
- **core/** — SSE transform, conversation state
- **mcp/** — MCP server for IDE agents
- **scripts/** — cookie harvest helper

## Quickstart

    pip install -r requirements.txt
    playwright install chromium
    cp .env.example .env          # edit API_KEY etc.
    echo "email:password" > accounts.txt
    python main.py

Or skip login automation — start empty and add a cookie:

    python main.py               # starts with 0 accounts
    python scripts/get_cookie.py # browser login → auto-add

## Use

    curl -N localhost:3000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "x-session-id: s1" \
      -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}],"stream":true}'

OpenAI SDK: base_url=http://localhost:3000/v1, api_key=$API_KEY.

## MCP (Antigravity)

    make register    # prints the config JSON

## Notes

- Keep the repo private — accounts + bypass internals.
- Upstream format changes break things; check chatgpt.com in a browser
  via Reqable when responses stop making sense.
