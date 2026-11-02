"""
JWT access_token lifecycle.

ChatGPT auth model:
- __Secure-next-auth.session-token cookie (~30d rolling)
- GET /api/auth/session with that cookie → fresh JWT access_token
- JWT expires ~10 days; re-fetch any time while cookie is valid
"""
import logging
from datetime import datetime, timedelta

import jwt

from config import Config
from core.exceptions import TokenExpiredError

log = logging.getLogger("auth")


class TokenManager:
    def __init__(self, cf_manager):
        self.cf = cf_manager
        self.tokens: dict[str, dict] = {}

    def add_direct_access_token(self, access_token: str, user_email: str = "direct@token") -> dict:
        """Add an already resolved JWT access_token directly."""
        try:
            payload = jwt.decode(access_token, options={"verify_signature": False})
            exp = payload.get("exp")
            expires = datetime.utcfromtimestamp(exp).isoformat() if exp else ""
        except Exception:
            expires = (datetime.utcnow() + timedelta(days=10)).isoformat()

        return {
            "access_token": access_token.strip(),
            "expires": expires,
            "user": {"email": user_email},
            "session_cookie": "",
        }

    def get_token_from_session_cookie(self, session_cookie: str) -> dict:
        """Exchange session cookie for a JWT access_token.
        Supports both single token and chunked tokens (.0 and .1 separated by || or chunked).
        """
        self.cf.ensure_valid()

        # Handle split chunked cookies (NextAuth splits large cookies across .0 and .1)
        if "||" in session_cookie:
            c0, c1 = session_cookie.split("||", 1)
            self.cf.session.cookies.set("__Secure-next-auth.session-token.0", c0.strip(), domain=".chatgpt.com")
            self.cf.session.cookies.set("__Secure-next-auth.session-token.1", c1.strip(), domain=".chatgpt.com")
            self.cf.session.cookies.set("__Secure-next-auth.session-token", (c0 + c1).strip(), domain=".chatgpt.com")
        else:
            self.cf.session.cookies.set(
                "__Secure-next-auth.session-token",
                session_cookie.strip(),
                domain=".chatgpt.com",
            )
            # In case Chrome chunking was simply concatenated:
            if len(session_cookie) > 3900:
                self.cf.session.cookies.set("__Secure-next-auth.session-token.0", session_cookie[:3967], domain=".chatgpt.com")
                self.cf.session.cookies.set("__Secure-next-auth.session-token.1", session_cookie[3967:], domain=".chatgpt.com")

        resp = self.cf.request(
            "GET",
            Config.UPSTREAM_SESSION,
            headers={
                "User-Agent": self.cf.user_agent,
                "Accept": "*/*",
                "Referer": f"{Config.UPSTREAM_BASE}/",
            },
            timeout=30,
        )

        if resp.status_code != 200:
            raise TokenExpiredError(
                f"Session fetch failed: HTTP {resp.status_code}"
            )

        data = resp.json()
        access_token = data.get("accessToken")
        if not access_token:
            raise TokenExpiredError("No accessToken in session response")

        return {
            "access_token": access_token,
            "expires": data.get("expires", ""),
            "user": data.get("user", {}),
            "session_cookie": session_cookie,
        }

    @staticmethod
    def decode_jwt_expiry(token: str) -> datetime:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return datetime.fromtimestamp(decoded["exp"])

    def is_token_expired(self, account_id: str) -> bool:
        if account_id not in self.tokens:
            return True
        token_data = self.tokens[account_id]
        expiry = self.decode_jwt_expiry(token_data["access_token"])
        margin = timedelta(hours=Config.REFRESH_MARGIN_HOURS)
        return datetime.now() >= expiry - margin

    def refresh_token(self, account_id: str) -> str:
        token_data = self.tokens[account_id]
        fresh = self.get_token_from_session_cookie(token_data["session_cookie"])
        self.tokens[account_id] = fresh
        log.info("Token refreshed for %s", account_id)
        return fresh["access_token"]

    def get_valid_token(self, account_id: str) -> str:
        if self.is_token_expired(account_id):
            return self.refresh_token(account_id)
        return self.tokens[account_id]["access_token"]
