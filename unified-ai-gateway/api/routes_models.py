import time
from fastapi import APIRouter

router = APIRouter()

ALL_MODELS = [
    # DeepSeek
    {"id": "deepseek-reasoner", "owned_by": "deepseek"},
    {"id": "deepseek-chat", "owned_by": "deepseek"},
    {"id": "deepseek-r1", "owned_by": "deepseek"},
    {"id": "deepseek-v3", "owned_by": "deepseek"},
    # Gemini
    {"id": "gemini-web", "owned_by": "google"},
    {"id": "gemini-2.5-flash", "owned_by": "google"},
    {"id": "gemini-2.5-pro", "owned_by": "google"},
    {"id": "gemini-2.0-flash", "owned_by": "google"},
    # ChatGPT
    {"id": "gpt-4o", "owned_by": "openai"},
    {"id": "gpt-4o-mini", "owned_by": "openai"},
    {"id": "o1", "owned_by": "openai"},
    {"id": "o1-mini", "owned_by": "openai"},
    {"id": "chatgpt-web", "owned_by": "openai"},
]


@router.get("/v1/models")
async def list_models():
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": m["id"],
                "object": "model",
                "created": now,
                "owned_by": m["owned_by"],
                "permission": [],
                "root": m["id"],
                "parent": None,
            }
            for m in ALL_MODELS
        ],
    }
