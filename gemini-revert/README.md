# gemini-gateway

Gemini API (chính thống, free tier) → OpenAI-compatible API → MCP tools cho IDE agent.

Không reverse engineering, không session harvesting — key của riêng bạn,
lấy miễn phí tại [aistudio.google.com](https://aistudio.google.com).

## Architecture

    [Antigravity / MCP client]
              │ MCP (stdio)
              ▼
    [mcp/mcp_server.py]
              │ HTTP — OpenAI format
              ▼
    [FastAPI gateway :3000]  ── x-api-key guard
              │ ProviderRouter (failover)
              ├──▶ Gemini API      (generativelanguage.googleapis.com)
              ├──▶ Groq API        (optional)
              └──▶ OpenRouter API  (optional)

## Quickstart

    pip install -r requirements.txt
    cp .env.example .env        # điền GEMINI_API_KEY + API_KEY
    python main.py

Test:

    curl -N localhost:3000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -d '{"model":"gemini-2.5-flash",
           "messages":[{"role":"user","content":"hi"}],"stream":true}'

OpenAI SDK: `base_url=http://localhost:3000/v1`, `api_key=$API_KEY`.

## Endpoints

| Route                | Method | Auth      | Mô tả                  |
|----------------------|--------|-----------|------------------------|
| /v1/chat/completions | POST   | x-api-key | chat, stream + non     |
| /v1/models           | GET    | x-api-key | models theo provider   |
| /health              | GET    | —         | liveness + provider list |

## Failover

`PROVIDER_ORDER=gemini,groq,openrouter` — hết quota / lỗi 5xx ở provider 1
tự chuyển provider 2, 3. Model không rõ nguồn rơi về `DEFAULT_MODEL`.
Tên cũ kiểu `gpt-4o` tự map sang Gemini tương đương (xem `ALIASES`).

## MCP (Antigravity)

    make register    # in ra config JSON

Tools: `llm_chat`, `llm_models`.

## Deploy

    docker compose up -d          # gateway + Caddy (TLS tự động)

GitHub Actions auto-build image lên GHCR mỗi push vào `main`.

## Rate limits

Free tier giới hạn theo model (flash hào phóng nhất). Số liệu hiện tại
xem trong AI Studio khi tạo key. Muốn cao hơn — thêm Groq/OpenRouter
vào failover chain là đủ cho agent workload.
