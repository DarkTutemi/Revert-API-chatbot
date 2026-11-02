import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", "3000"))
    API_KEY = os.getenv("API_KEY", "sk-unified-local-gateway-key")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-reasoner")
