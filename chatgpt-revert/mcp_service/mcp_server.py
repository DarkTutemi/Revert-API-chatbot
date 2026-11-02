"""
MCP stdio server — exposes the proxy as tools for IDE agents
(Antigravity, Cursor, Claude Desktop, anything MCP-compatible).
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

PROXY_URL = os.getenv("PROXY_URL", "http://localhost:3000")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", os.getenv("API_KEY", "change-me-to-a-long-random-string"))

app = Server("chatgpt-proxy")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="chatgpt_chat",
            description=(
                "Chat with ChatGPT via private proxy. Use for a second "
                "opinion, delegated reasoning, or cross-model review. "
                "Reuse session_id to continue a conversation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to send",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for conversation continuity",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model slug (gpt-4o, gpt-4o-mini)",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="chatgpt_models",
            description="List available models on the proxy",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": PROXY_API_KEY,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        if name == "chatgpt_chat":
            session_id = arguments.get("session_id", "default")
            resp = await client.post(
                f"{PROXY_URL}/v1/chat/completions",
                headers={**headers, "x-session-id": session_id},
                json={
                    "model": arguments.get("model", "gpt-4o"),
                    "messages": [
                        {"role": "user", "content": arguments["message"]}
                    ],
                    "stream": False,
                },
            )
            if resp.status_code != 200:
                return [TextContent(
                    type="text",
                    text=f"Proxy error {resp.status_code}: {resp.text[:500]}",
                )]
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return [TextContent(type="text", text=content)]

        elif name == "chatgpt_models":
            resp = await client.get(f"{PROXY_URL}/v1/models", headers=headers)
            if resp.status_code != 200:
                return [TextContent(
                    type="text",
                    text=f"Proxy error {resp.status_code}",
                )]
            ids = [m["id"] for m in resp.json()["data"]]
            return [TextContent(type="text", text=json.dumps(ids))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="chatgpt-proxy",
                server_version="1.0.0",
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
