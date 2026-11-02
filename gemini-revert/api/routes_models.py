from fastapi import APIRouter

router = APIRouter()

providers: dict = {}   # injected
models: dict = {}      # injected: provider_name → [model_ids]


@router.get("/v1/models")
async def list_models():
    data = []
    for provider_name, model_list in models.items():
        if provider_name in providers:
            data.extend(
                {"id": mid, "object": "model", "owned_by": provider_name}
                for mid in model_list
            )
    return {"object": "list", "data": data}
