import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from providers.deepseek_web import DeepSeekWebProvider
from api.middleware import ApiKeyMiddleware
from api import routes_chat, routes_models, routes_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

deepseek_provider = DeepSeekWebProvider()
routes_chat.provider_instance = deepseek_provider

app = FastAPI(title="deepseek-gateway", version="1.0.0")

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
app.include_router(routes_bridge.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "deepseek-gateway",
        "port": Config.PORT,
        "default_model": Config.DEFAULT_MODEL
    }
