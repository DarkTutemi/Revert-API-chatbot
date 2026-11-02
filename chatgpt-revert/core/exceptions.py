class ProxyError(Exception):
    """Base error for the proxy stack."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CloudflareBlockedError(ProxyError):
    def __init__(self, message: str = "Cloudflare challenge could not be bypassed"):
        super().__init__(message, status_code=502)


class TokenExpiredError(ProxyError):
    def __init__(self, message: str = "Access token expired and refresh failed"):
        super().__init__(message, status_code=401)


class RateLimitError(ProxyError):
    def __init__(self, message: str = "Rate limited by upstream"):
        super().__init__(message, status_code=429)


class NoAccountsError(ProxyError):
    def __init__(self, message: str = "No accounts available in token pool"):
        super().__init__(message, status_code=503)
