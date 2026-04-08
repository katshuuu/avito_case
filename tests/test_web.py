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


def test_analyze_demo_returns_steps_and_download():
    client = TestClient(app)
    r = client.post(
        "/api/analyze_demo",
        json={
            "description": "Электрика отдельно, сантехника отдельно.",
            "mcId": 101,
            "mcTitle": "Ремонт квартир и домов под ключ",
            "use_llm_drafts": False,
            "async_drafts": False,
            "demo_mode": True,
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert "result" in payload
    assert "steps" in payload
    assert "downloadUrl" in payload
    dl = client.get(payload["downloadUrl"])
    assert dl.status_code == 200
    assert "detectedMcIds" in dl.json()


def test_demo_samples_endpoint_and_sample_based_demo():
    client = TestClient(app)
    rs = client.get("/api/demo_samples")
    assert rs.status_code == 200
    samples = rs.json().get("samples", [])
    assert len(samples) >= 1
    sample_id = samples[0]["id"]

    r = client.post(
        "/api/analyze_demo",
        json={
            "description": "этот текст должен игнорироваться в demo",
            "mcId": 999,
            "mcTitle": "Игнор",
            "use_llm_drafts": False,
            "async_drafts": False,
            "demo_mode": True,
            "demo_sample_id": sample_id,
        },
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("sample", {}).get("id") == sample_id
