import pytest

from auth.token_pool import TokenPool
from core.exceptions import NoAccountsError


class FakeTokenManager:
    def __init__(self):
        self.tokens = {}

    def get_token_from_session_cookie(self, cookie):
        return {"access_token": f"tok-{cookie}", "user": {"email": "t@t.co"},
                "session_cookie": cookie}

    def get_valid_token(self, account_id):
        return self.tokens[account_id]["access_token"]


def test_add_and_rotate():
    tm = FakeTokenManager()
    pool = TokenPool(tm)
    pool.add_account("a1", "cookie-1")
    pool.add_account("a2", "cookie-2")

    results = {pool.next_token()[1] for _ in range(4)}
    assert results == {"a1", "a2"}


def test_empty_pool_raises():
    pool = TokenPool(FakeTokenManager())
    with pytest.raises(NoAccountsError):
        pool.next_token()


def test_cooldown_removes_account():
    tm = FakeTokenManager()
    pool = TokenPool(tm)
    pool.add_account("a1", "cookie-1")
    pool.add_account("a2", "cookie-2")
    pool.mark_rate_limited("a1", cooldown_seconds=9999)

    assert pool.active_count == 1
    seen = {pool.next_token()[1] for _ in range(4)}
    assert seen == {"a2"}
