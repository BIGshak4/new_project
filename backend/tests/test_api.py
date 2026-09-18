from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["engine_version"]


def test_catalog_summary_reports_valid_seeds():
    body = client.get("/catalog/summary").json()
    assert body["valid"] is True
    assert body["skills"] >= 30 and "digital-hardware-engineer" in body["roles"] and body["questions"] >= 3
