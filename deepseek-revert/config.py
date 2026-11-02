import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", "3002"))
    API_KEY = os.getenv("API_KEY", "sk-deepseek-local-key")

    PROVIDER_ORDER = [
        p.strip()
        for p in os.getenv("PROVIDER_ORDER", "deepseek-web").split(",")
        if p.strip()
    ]
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-reasoner")
