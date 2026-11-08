"""Test-only access configuration. Never contains a real provider credential."""
import pytest


@pytest.fixture
def enabled_api(monkeypatch):
    monkeypatch.setenv("EXCEPTIONFORGE_ENABLE_LIVE", "true")
    monkeypatch.setenv("EXCEPTIONFORGE_ACCESS_TOKEN", "T" * 40)
    monkeypatch.setenv("VULTR_INFERENCE_API_KEY", "TEST_ONLY_NOT_REAL")
    return {"Authorization": "Bearer " + "T" * 40}

@pytest.fixture(autouse=True)
def isolated_rate_limit_state():
    """Each regression test starts with a clean process-wide test quota."""
    from app.access import live_limiter, local_limiter
    live_limiter.reset_for_tests()
    local_limiter.reset_for_tests()
    yield
    live_limiter.reset_for_tests()
    local_limiter.reset_for_tests()
