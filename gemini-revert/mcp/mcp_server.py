"""
MCP stdio server — exposes the gateway as tools for IDE agents
(Antigravity, Cursor, Claude Desktop, anything MCP-compatible).
"""
import asyncio
import json
import os
import sys

# Ensure global mcp package is imported, not local folder
if os.path.dirname(__file__) in sys.path:
    sys.path.remove(os.path.dirname(__file__))

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

PROXY_URL = os.getenv("PROXY_URL", "http://localhost:3000")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", os.getenv("API_KEY", "change-me"))

app = Server("gemini-gateway")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="llm_chat",
            description=(
                "Chat with an LLM (default Gemini) via private gateway. "
                "Use for a second opinion, delegated reasoning, or cross-model "
                "review. Defaults to gemini-2.5-flash; other models available "
                "via llm_models."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to send",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model id (optional, default gemini-2.5-flash)",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="llm_models",
            description="List available models on the gateway",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    headers = {"Content-Type": "application/json", "x-api-key": PROXY_API_KEY}

    async with httpx.AsyncClient(timeout=180) as client:
        if name == "llm_chat":
            resp = await client.post(
                f"{PROXY_URL}/v1/chat/completions",
                headers=headers,
                json={
                    "model": arguments.get("model", "gemini-2.5-flash"),
                    "messages": [{"role": "user", "content": arguments["message"]}],
                    "stream": False,
                },
            )
            if resp.status_code != 200:
                return [TextContent(
                    type="text",
                    text=f"Gateway error {resp.status_code}: {resp.text[:500]}",
                )]
            return [TextContent(
                type="text",
                text=resp.json()["choices"][0]["message"]["content"],
            )]

        elif name == "llm_models":
            resp = await client.get(f"{PROXY_URL}/v1/models", headers=headers)
            if resp.status_code != 200:
                return [TextContent(type="text", text=f"Gateway error {resp.status_code}")]
            ids = [m["id"] for m in resp.json()["data"]]
            return [TextContent(type="text", text=json.dumps(ids))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-gateway",
                server_version="1.0.0",
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
