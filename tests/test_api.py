import io
from fastapi.testclient import TestClient
from app.main import app


def test_health_honestly_reports_unverified_vultr():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["vultr_deployment"] == "not-verified"


def test_no_api_key_cannot_fake_result(monkeypatch):
    monkeypatch.delenv("VULTR_INFERENCE_API_KEY", raising=False)
    client = TestClient(app)
    files = {
        "purchase_orders": ("po.csv", b"A,B\nx,y\n", "text/csv"),
        "goods_receipts": ("gr.csv", b"A,B\nx,y\n", "text/csv"),
        "invoices": ("inv.csv", b"Bill Number,Notes\nINV-1,test\n", "text/csv"),
    }
    response = client.post("/api/analyse", files=files)
    assert response.status_code == 503
    assert "NOT attempted" in response.json()["detail"]


def test_single_screen_is_present():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert "Run local analysis" in r.text
    assert "Vultr AI (live)" in r.text
    assert 'lang="en-GB"' in r.text

def test_rejects_empty_file_before_model(monkeypatch):
    monkeypatch.delenv("VULTR_INFERENCE_API_KEY", raising=False)
    r = TestClient(app).post("/api/analyse", files={
        "purchase_orders": ("empty.csv", b"", "text/csv"),
        "goods_receipts": ("gr.csv", b"A,B\nx,y\n", "text/csv"),
        "invoices": ("inv.csv", b"Bill Number,Notes\nINV-1,test\n", "text/csv"),
    })
    assert r.status_code == 422
