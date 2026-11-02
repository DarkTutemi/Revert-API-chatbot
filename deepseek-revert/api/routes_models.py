import time
from fastapi import APIRouter

router = APIRouter()

DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-v3",
    "deepseek-r1"
]


@router.get("/v1/models")
async def list_models():
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": mid,
                "object": "model",
                "created": now,
                "owned_by": "deepseek",
                "permission": [],
                "root": mid,
                "parent": None,
            }
            for mid in DEEPSEEK_MODELS
        ],
    }
