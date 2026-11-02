import uvicorn
from dotenv import load_dotenv

load_dotenv()

from config import Config

if __name__ == "__main__":
    print(f"[*] Starting DeepSeek Gateway on port {Config.PORT}...")
    print(f"[*] Default Model: {Config.DEFAULT_MODEL}")
    uvicorn.run("api.app:app", host="0.0.0.0", port=Config.PORT)
