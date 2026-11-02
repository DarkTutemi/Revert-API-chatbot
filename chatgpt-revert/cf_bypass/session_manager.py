"""
Cloudflare session lifecycle manager.

Strategy:
1. curl_cffi session impersonating Chrome TLS fingerprint (fast, no browser)
2. If challenge escalates (Turnstile) → Playwright browser solver fallback
3. Extract cf_clearance + matching User-Agent
4. Monitor validity, re-acquire on 403
"""
import time
import threading
import logging

from curl_cffi.requests import Session

from config import Config
from cf_bypass.browser_solver import solve_challenge_via_browser

log = logging.getLogger("cf_bypass")


class CFSessionManager:
    def __init__(self):
        self.session: Session | None = None
        self.cf_clearance: str | None = None
        self.user_agent: str = Config.USER_AGENT
        self._lock = threading.Lock()
        self._last_check = 0.0

    def _init_session(self):
        self.session = Session(impersonate=Config.CF_IMPERSONATE)

    def acquire(self) -> bool:
        """Acquire CF clearance. Lightweight first, browser fallback."""
        with self._lock:
            # Attempt 1: curl_cffi direct — works for most residential IPs
            self._init_session()
            try:
                resp = self.session.get(
                    Config.UPSTREAM_BASE,
                    headers=Config.BASE_HEADERS,
                    timeout=30,
                )
                clearance = self._extract_clearance()
                if clearance or resp.status_code == 200:
                    log.info("CF check via curl_cffi: OK (status=%s, clearance=%s)", resp.status_code, bool(clearance))
                    self._last_check = time.time()
                    return True
                log.warning("curl_cffi got no clearance (status=%s), escalating", resp.status_code)
            except Exception as e:
                log.warning("curl_cffi attempt failed: %s", e)

            # Attempt 2: real browser via Playwright
            log.info("Escalating to Playwright browser solver...")
            result = solve_challenge_via_browser(Config.UPSTREAM_BASE)
            if not result:
                log.error("Browser solver also failed — CF bypass FAILED")
                return False

            self.cf_clearance = result["cf_clearance"]
            self.user_agent = result["user_agent"]

            # Rebuild session, inject browser cookies + matching UA
            self._init_session()
            self.session.cookies.set(
                "cf_clearance", self.cf_clearance, domain=".chatgpt.com"
            )
            self._last_check = time.time()
            log.info("CF bypass via browser: OK")
            return True

    def _extract_clearance(self) -> str | None:
        if not self.session:
            return None
        # curl_cffi cookies can be dict-like or CookieJar
        val = None
        if hasattr(self.session.cookies, "get"):
            val = self.session.cookies.get("cf_clearance")
        if not val:
            for cookie in self.session.cookies:
                name = getattr(cookie, "name", str(cookie))
                if name == "cf_clearance":
                    val = getattr(cookie, "value", self.session.cookies[cookie] if cookie in self.session.cookies else str(cookie))
                    break
        if val:
            self.cf_clearance = val
            self._last_check = time.time()
            return val
        return None

    def is_valid(self) -> bool:
        """Probe the session endpoint — 403 means clearance is dead."""
        if not self.cf_clearance and not self.session:
            return False
        try:
            resp = self.session.get(
                Config.UPSTREAM_SESSION,
                headers={**Config.BASE_HEADERS, "User-Agent": self.user_agent},
                timeout=15,
            )
            return resp.status_code != 403
        except Exception:
            return False

    def ensure_valid(self):
        """Re-acquire if stale or dead. Called before every upstream request."""
        elapsed = time.time() - self._last_check
        if elapsed > Config.CF_CHECK_INTERVAL and not self.is_valid():
            log.info("CF clearance expired, re-acquiring...")
            self.acquire()
        self._last_check = time.time()

    def request(self, method: str, url: str, **kwargs):
        """
        Wrapper — injects CF context, retries once on 403 challenge.
        """
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self.user_agent)

        resp = self.session.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 403 and "cf-mitigated" in resp.headers:
            log.warning("CF challenge mid-flight, re-acquiring and retrying once")
            self.acquire()
            resp = self.session.request(method, url, headers=headers, **kwargs)

        return resp
