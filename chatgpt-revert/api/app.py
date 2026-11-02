"""
FastAPI app assembly with CORS and Browser Bridge support.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from cf_bypass.session_manager import CFSessionManager
from auth.token_manager import TokenManager
from auth.token_pool import TokenPool
from core.conversation import ConversationStore

from api.middleware import ApiKeyMiddleware
from api import routes_chat, routes_models, routes_admin, routes_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Singletons
cf_manager = CFSessionManager()
token_manager = TokenManager(cf_manager)
token_pool = TokenPool(token_manager)
conversation_store = ConversationStore()

# Dependency injection into route modules
routes_chat.cf_manager = cf_manager
routes_chat.token_pool = token_pool
routes_chat.conversation_store = conversation_store

routes_admin.cf_manager = cf_manager
routes_admin.token_pool = token_pool
routes_admin.token_manager = token_manager
routes_admin.conversation_store = conversation_store

app = FastAPI(title="chatgpt-proxy", version="1.0.0")

# Enable CORS for browser bridge
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApiKeyMiddleware)

app.include_router(routes_chat.router)
app.include_router(routes_models.router)
app.include_router(routes_admin.router)
app.include_router(routes_bridge.router)


@app.get("/health")
async def health():
    """Unauthenticated liveness probe."""
    return {"status": "ok"}
