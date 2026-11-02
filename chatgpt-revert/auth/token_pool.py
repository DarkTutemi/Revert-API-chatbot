"""
Rotating multi-account pool.
Distributes load and survives per-account rate limits.
"""
import itertools
import threading
import time
import logging

from auth.token_manager import TokenManager
from core.exceptions import NoAccountsError

log = logging.getLogger("pool")


class TokenPool:
    def __init__(self, token_manager: TokenManager):
        self.tm = token_manager
        self.accounts: list[str] = []
        self._cooldown: set[str] = set()
        self._cycle = None
        self._lock = threading.Lock()

    def add_account(self, account_id: str, session_cookie: str, access_token: str | None = None):
        if access_token:
            token_data = self.tm.add_direct_access_token(access_token)
        elif session_cookie.startswith("eyJhbGciOiJSUzI1Ni") or session_cookie.startswith("eyJh"):
            # Check if user passed JWT directly as session_cookie
            try:
                import jwt
                payload = jwt.decode(session_cookie, options={"verify_signature": False})
                if "https://api.openai.com/profile" in payload or "exp" in payload:
                    token_data = self.tm.add_direct_access_token(session_cookie)
                else:
                    token_data = self.tm.get_token_from_session_cookie(session_cookie)
            except Exception:
                token_data = self.tm.get_token_from_session_cookie(session_cookie)
        else:
            token_data = self.tm.get_token_from_session_cookie(session_cookie)

        self.tm.tokens[account_id] = token_data
        with self._lock:
            self.accounts.append(account_id)
            self._rebuild_cycle()
        email = token_data.get("user", {}).get("email", "unknown")
        log.info("Account added: %s (%s)", account_id, email)

    def _rebuild_cycle(self):
        active = [a for a in self.accounts if a not in self._cooldown]
        self._cycle = itertools.cycle(active) if active else None

    def next_token(self) -> tuple[str, str]:
        """Returns (access_token, account_id) — round-robin."""
        with self._lock:
            if not self._cycle:
                raise NoAccountsError()
            account_id = next(self._cycle)
        token = self.tm.get_valid_token(account_id)
        return token, account_id

    def mark_rate_limited(self, account_id: str, cooldown_seconds: int = 3600):
        """Temporarily pull an account out of rotation."""
        with self._lock:
            self._cooldown.add(account_id)
            self._rebuild_cycle()
        log.warning("Account %s rate-limited, cooldown %ss", account_id, cooldown_seconds)

        def _re_add():
            time.sleep(cooldown_seconds)
            with self._lock:
                self._cooldown.discard(account_id)
                self._rebuild_cycle()
            log.info("Account %s back in rotation", account_id)

        threading.Thread(target=_re_add, daemon=True).start()

    @property
    def active_count(self) -> int:
        with self._lock:
            return len([a for a in self.accounts if a not in self._cooldown])
