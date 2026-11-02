import uvicorn
from dotenv import load_dotenv

load_dotenv()

from config import Config

if __name__ == "__main__":
    print(f"=====================================================")
    print(f"   UNIFIED AI REVERSE PROXY GATEWAY (Port {Config.PORT})")
    print(f"   Supported Platforms: ChatGPT | Gemini | DeepSeek")
    print(f"   Single API: http://localhost:{Config.PORT}/v1/chat/completions")
    print(f"=====================================================")
    uvicorn.run("api.app:app", host="0.0.0.0", port=Config.PORT)
