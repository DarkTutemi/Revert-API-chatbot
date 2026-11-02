from fastapi import APIRouter

router = APIRouter()

MODELS = [
    ("gpt-4o", "openai"),
    ("gpt-4o-mini", "openai"),
    ("gpt-4-turbo", "openai"),
    ("gpt-4", "openai"),
    ("gpt-3.5-turbo", "openai"),
    ("o1", "openai"),
]


@router.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": mid, "object": "model", "owned_by": owner}
            for mid, owner in MODELS
        ],
    }
