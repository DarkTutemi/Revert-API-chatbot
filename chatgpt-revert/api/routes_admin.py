from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Injected at app assembly
token_pool = None
token_manager = None
cf_manager = None
conversation_store = None


class AddAccountRequest(BaseModel):
    session_cookie: str | None = None
    access_token: str | None = None


@router.post("/admin/add-account")
async def add_account(request: AddAccountRequest):
    import uuid
    account_id = f"acct_{uuid.uuid4().hex[:8]}"
    try:
        token_pool.add_account(account_id, request.session_cookie or "", request.access_token)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    return {"status": "added", "account_id": account_id}


@router.get("/admin/status")
async def status():
    return {
        "accounts_total": len(token_pool.accounts),
        "accounts_active": token_pool.active_count,
        "accounts_cooldown": len(token_pool._cooldown),
        "tokens_tracked": len(token_manager.tokens),
        "cf_valid": cf_manager.is_valid() if cf_manager.session else False,
        "conversations": conversation_store.count,
    }


@router.post("/admin/reset-conversation/{session_id}")
async def reset_conversation(session_id: str):
    conversation_store.reset(session_id)
    return {"status": "reset", "session_id": session_id}
