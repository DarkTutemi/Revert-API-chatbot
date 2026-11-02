from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import Config


class ApiKeyMiddleware(BaseHTTPMiddleware):
    PROTECTED = ("/v1",)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(self.PROTECTED):
            auth_header = request.headers.get("authorization", "")
            token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else request.headers.get("x-api-key")
            if token != Config.API_KEY:
                return JSONResponse(
                    {"error": {"message": "unauthorized", "type": "auth_error"}},
                    status_code=401,
                )
        return await call_next(request)
