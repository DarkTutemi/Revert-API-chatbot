import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from providers import GeminiProvider, GeminiWebProvider, GroqProvider, OpenRouterProvider, ProviderRouter
from providers.gemini import MODELS as GEMINI_MODELS
from providers.groq import MODELS as GROQ_MODELS
from providers.openrouter import MODELS as OR_MODELS

from api.middleware import ApiKeyMiddleware
from api import routes_chat, routes_models, routes_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

providers = {}
if Config.GEMINI_API_KEY:
    providers["gemini"] = GeminiProvider(Config.GEMINI_API_KEY)
if Config.GROQ_API_KEY:
    providers["groq"] = GroqProvider(Config.GROQ_API_KEY)
if Config.OPENROUTER_API_KEY:
    providers["openrouter"] = OpenRouterProvider(Config.OPENROUTER_API_KEY)

# Always add GeminiWebProvider as fallback or primary web bridge
providers["gemini-web"] = GeminiWebProvider()

order = [p for p in Config.PROVIDER_ORDER if p in providers]
if "gemini-web" not in order:
    order.append("gemini-web")

router_obj = ProviderRouter(
    providers=providers,
    default_order=order,
    default_model=Config.DEFAULT_MODEL,
)

routes_chat.router_obj = router_obj
routes_models.providers = providers
routes_models.models = {
    "gemini": GEMINI_MODELS,
    "gemini-web": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-web"],
    "groq": GROQ_MODELS,
    "openrouter": OR_MODELS,
}

app = FastAPI(title="gemini-gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiKeyMiddleware)

app.include_router(routes_bridge.router)
app.include_router(routes_chat.router)
app.include_router(routes_models.router)


@app.get("/health")
async def health():
    return {"status": "ok", "providers": list(providers.keys())}
