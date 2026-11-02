import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", "3001"))
    API_KEY = os.getenv("API_KEY", "change-me")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    PROVIDER_ORDER = [
        p.strip()
        for p in os.getenv("PROVIDER_ORDER", "gemini,groq,openrouter").split(",")
        if p.strip()
    ]
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
