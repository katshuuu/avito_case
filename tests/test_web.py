import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from web.app import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_returns_contract():
    client = TestClient(app)
    r = client.post(
        "/api/analyze",
        json={
            "description": "Ремонт под ключ, электрика отдельно, сантехника отдельно.",
            "mcId": 101,
            "mcTitle": "Ремонт квартир и домов под ключ",
            "use_llm_drafts": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "detectedMcIds" in data
    assert "shouldSplit" in data
    assert "drafts" in data
    assert isinstance(data["drafts"], list)


def test_analyze_async_drafts_contract():
    client = TestClient(app)
    r = client.post(
        "/api/analyze",
        json={
            "description": "Электрика отдельно, сантехника отдельно.",
            "mcId": 101,
            "mcTitle": "Ремонт квартир и домов под ключ",
            "use_llm_drafts": True,
            "async_drafts": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "detectedMcIds" in data
    assert "shouldSplit" in data
    assert "drafts" in data
    assert data["drafts"] == []
    assert "draftJobId" in data
