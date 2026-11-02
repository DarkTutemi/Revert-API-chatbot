import uvicorn
from dotenv import load_dotenv

load_dotenv()

from config import Config

if __name__ == "__main__":
    from api.app import providers
    print(f"[*] Starting Gemini Gateway on port {Config.PORT}...")
    print(f"[*] Active providers: {list(providers.keys())}")
    uvicorn.run("api.app:app", host="0.0.0.0", port=Config.PORT)
