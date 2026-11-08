"""Stage 2.2 security tests; network, Vultr and Docker are never contacted."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from app import main, sandbox
from app.access import SlidingLimiter, local_limiter, live_limiter
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "T" * 40


def files():
    return {
        field: (filename, (ROOT / "demo_data" / filename).read_bytes(), "text/csv")
        for field, filename in [
            ("purchase_orders", "purchase_orders.csv"),
            ("goods_receipts", "goods_receipts.csv"),
            ("invoices", "invoices.csv"),
        ]
    }


def test_disabled_live_cannot_call_model_even_when_key_is_present(monkeypatch, enabled_api):
    monkeypatch.delenv("EXCEPTIONFORGE_ENABLE_LIVE", raising=False)
    monkeypatch.setattr(main, "analyse", lambda *_a, **_k: pytest.fail("Billed API invoked"))
    monkeypatch.setattr(main, "require_docker_ready", lambda: pytest.fail("Docker invoked"))
    response = TestClient(app).post("/api/analyse", files=files(), headers=enabled_api)
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"]
    assert response.headers["cache-control"] == "no-store"


def test_live_token_not_configured_or_too_short_fails_closed(monkeypatch, enabled_api):
    monkeypatch.delenv("EXCEPTIONFORGE_ACCESS_TOKEN", raising=False)
    r = TestClient(app).post("/api/analyse", files=files(), headers=enabled_api)
    assert r.status_code == 503 and "not safely configured" in r.json()["detail"]
    monkeypatch.setenv("EXCEPTIONFORGE_ACCESS_TOKEN", "short")
    r = TestClient(app).post("/api/containment-probe", headers=enabled_api)
    assert r.status_code == 503


@pytest.mark.parametrize("authorization", [None, "Bearer incorrect", "Bearer " + "x" * 40, "Basic " + TOKEN, "Bearer " + TOKEN + "x"])
def test_invalid_or_missing_token_never_executes_any_live_operation(monkeypatch, enabled_api, authorization):
    monkeypatch.setattr(main, "analyse", lambda *_a, **_k: pytest.fail("Billed API invoked"))
    monkeypatch.setattr(main, "require_docker_ready", lambda: pytest.fail("Docker invoked"))
    monkeypatch.setattr(main, "containment_probe", lambda *_a, **_k: pytest.fail("Probe invoked"))
    headers = {"Authorization": authorization} if authorization is not None else {}
    with TestClient(app) as client:
        for path in ("/api/analyse", "/api/containment-probe"):
            r = client.post(path, headers=headers, files=files() if path.endswith("analyse") else None)
            assert r.status_code == 401, (path, r.text)
            assert TOKEN not in r.text


def test_querystring_cannot_supply_live_token(monkeypatch, enabled_api):
    r = TestClient(app).post("/api/containment-probe?access_token=" + TOKEN)
    assert r.status_code == 401


def test_missing_model_key_does_not_count_as_attempt(monkeypatch, enabled_api):
    monkeypatch.delenv("VULTR_INFERENCE_API_KEY", raising=False)
    monkeypatch.setattr(main, "require_docker_ready", lambda: pytest.fail("Docker preflight called"))
    r = TestClient(app).post("/api/analyse", files=files(), headers=enabled_api)
    assert r.status_code == 503 and "NOT attempted" in r.text
    assert not live_limiter._daily


def test_valid_authorisation_still_preflights_docker_before_model(monkeypatch, enabled_api):
    monkeypatch.setattr(main, "analyse", lambda *_a, **_k: pytest.fail("Billed API invoked"))
    def fail_docker():
        raise sandbox.SandboxError("Docker daemon unavailable. Vultr inference was NOT attempted")
    monkeypatch.setattr(main, "require_docker_ready", fail_docker)
    response = TestClient(app).post("/api/analyse", files=files(), headers=enabled_api)
    assert response.status_code == 503
    assert "NOT attempted" in response.json()["detail"]


def test_authorised_mocked_inference_flow_without_vultr_or_docker(monkeypatch, enabled_api):
    calls = []
    monkeypatch.setattr(main, "require_docker_ready", lambda: calls.append("preflight"))
    def fake_analyse(directory, *, validate_report):
        calls.append("inference_stub")
        report = validate_report({"findings": [], "analysed_invoices": 32})
        return {"report": report, "model": "fake-only", "code": "print('{}')", "attempts": 1, "sandbox": {"docker_invoked": False}}
    monkeypatch.setattr(main, "analyse", fake_analyse)
    response = TestClient(app).post("/api/analyse", files=files(), headers=enabled_api)
    assert response.status_code == 200, response.text
    assert calls == ["preflight", "inference_stub"]
    assert response.json()["model"] == "fake-only"
    assert response.headers["cache-control"] == "no-store"


def test_probe_requires_token_and_passes_only_real_returned_value(monkeypatch, enabled_api):
    calls = []
    monkeypatch.setattr(main, "containment_probe", lambda *_a, **_k: (calls.append(1) or {"passed": False, "probe": {"network_probe": "INDETERMINATE"}}))
    assert TestClient(app).post("/api/containment-probe").status_code == 401
    r = TestClient(app).post("/api/containment-probe", headers=enabled_api)
    assert r.status_code == 200 and r.json()["passed"] is False
    assert calls == [1]


def test_live_hourly_quota_blocks_fifth_request_before_inference(monkeypatch, enabled_api):
    calls = []
    monkeypatch.setattr(main, "require_docker_ready", lambda: None)
    monkeypatch.setattr(main, "analyse", lambda *_a, **_k: (calls.append(1) or {"report": {"findings": [], "analysed_invoices": 1}, "model": "mock", "attempts": 1, "code": "", "sandbox": {}}))
    client = TestClient(app)
    for _ in range(4):
        assert client.post("/api/analyse", files=files(), headers=enabled_api).status_code == 200
    rejected = client.post("/api/analyse", files=files(), headers=enabled_api)
    assert rejected.status_code == 429
    assert rejected.headers.get("retry-after")
    assert len(calls) == 4


def test_docker_probe_shares_live_budget(monkeypatch, enabled_api):
    monkeypatch.setattr(main, "containment_probe", lambda *_a, **_k: {"passed": False})
    client = TestClient(app)
    for _ in range(4):
        assert client.post("/api/containment-probe", headers=enabled_api).status_code == 200
    assert client.post("/api/containment-probe", headers=enabled_api).status_code == 429


def test_rate_limiter_concurrency_hourly_daily_and_recovery():
    clock = [100.0]
    gate = SlidingLimiter(per_window=2, window_seconds=60, per_day=3, max_active=1, clock=lambda: clock[0])
    first, retry = gate.reserve()
    assert first is not None and retry == 0
    second, retry = gate.reserve()
    assert second is None and retry == 2  # concurrency denial
    first.release(); first.release()  # idempotent release
    second, retry = gate.reserve()
    assert second is not None and retry == 0
    second.release()
    assert gate.reserve()[0] is None  # 2/60 seconds consumed
    clock[0] += 61
    third, _ = gate.reserve()
    assert third is not None
    third.release()
    assert gate.reserve()[0] is None  # 3/day consumed
    clock[0] += 86_401
    refreshed, retry = gate.reserve()
    assert refreshed is not None and retry == 0
    refreshed.release()


def test_local_demo_no_credentials_and_synthetic_samples_untouched(monkeypatch):
    monkeypatch.delenv("VULTR_INFERENCE_API_KEY", raising=False)
    monkeypatch.delenv("EXCEPTIONFORGE_ENABLE_LIVE", raising=False)
    monkeypatch.delenv("EXCEPTIONFORGE_ACCESS_TOKEN", raising=False)
    client = TestClient(app)
    assert client.get("/api/demo-data/invoices.csv").status_code == 200
    response = client.post("/api/local-analyse", files=files())
    assert response.status_code == 200
    assert response.json()["engine"] == "local_rules"
    assert len(response.json()["report"]["findings"]) == 15


def test_frontend_has_token_input_only_not_embedded_secret_or_persistent_storage():
    html = TestClient(app).get("/").text
    assert 'type="password"' in html
    assert 'name="access_token_ui_only"' in html
    assert "authHeaders()" in html
    assert "localStorage" not in html and "sessionStorage" not in html
    assert TOKEN not in html


def test_docker_preflight_fails_without_cli(monkeypatch):
    monkeypatch.setattr(sandbox.shutil, "which", lambda *_: None)
    with pytest.raises(sandbox.SandboxError, match="NOT attempted"):
        sandbox.require_docker_ready()


def test_docker_preflight_fails_when_daemon_or_image_missing(monkeypatch):
    monkeypatch.setattr(sandbox.shutil, "which", lambda *_: "/usr/bin/docker")
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0 if len(calls) == 1 else 1)
    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)
    with pytest.raises(sandbox.SandboxError, match="image not available"):
        sandbox.require_docker_ready()
    assert calls[0][1] == "info" and calls[1][1:3] == ["image", "inspect"]


def test_docker_preflight_does_not_touch_model_api(monkeypatch):
    monkeypatch.setattr(sandbox.shutil, "which", lambda *_: "/usr/bin/docker")
    monkeypatch.setattr(sandbox.subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=0))
    assert sandbox.require_docker_ready() is None
