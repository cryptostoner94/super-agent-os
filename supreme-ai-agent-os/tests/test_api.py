from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_capabilities():
    r = client.get("/capabilities")
    assert r.status_code == 200
    assert "llm" in r.json()

def test_agents():
    r = client.get("/agents")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_blocked_command():
    r = client.post("/system/exec", json={"command": "rm -rf /", "timeout": 5})
    assert r.status_code == 200
    assert r.json()["returncode"] == 126
