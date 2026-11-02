from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import Config
from core.exceptions import ProxyError


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Guards /v1/* and /admin/* behind x-api-key or Authorization: Bearer <key>."""

    PROTECTED = ("/v1", "/admin")

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(self.PROTECTED):
            auth_header = request.headers.get("authorization", "")
            bearer_token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
            api_key = request.headers.get("x-api-key") or bearer_token

            if api_key != Config.API_KEY:
                return JSONResponse(
                    {"error": {"message": "unauthorized", "type": "auth_error"}},
                    status_code=401,
                )
        try:
            return await call_next(request)
        except ProxyError as e:
            return JSONResponse(
                {"error": {"message": e.message, "type": "proxy_error"}},
                status_code=e.status_code,
            )
