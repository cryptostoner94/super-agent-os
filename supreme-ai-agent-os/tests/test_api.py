"""
Supreme AI Agent OS - API Tests
Comprehensive test suite for all API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

class TestHealth:
    """Health check endpoints"""
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "timestamp" in response.json()
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_readiness_probe(self):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] == True
    
    def test_liveness_probe(self):
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json()["alive"] == True

class TestCapabilities:
    """Capability endpoints"""
    
    def test_get_capabilities(self):
        response = client.get("/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "llm" in data
        assert "connectors" in data
    
    def test_capabilities_structure(self):
        response = client.get("/capabilities")
        data = response.json()
        assert isinstance(data.get("llm"), dict)

class TestAgents:
    """Agent endpoints"""
    
    def test_get_agents(self):
        response = client.get("/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_agent_run_minimal(self):
        response = client.post(
            "/agent/run",
            json={"prompt": "Hello", "agent_id": "executive"}
        )
        assert response.status_code == 200

class TestSkills:
    """Skills endpoints"""
    
    def test_get_skills(self):
        response = client.get("/skills")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestConnectors:
    """Connector endpoints"""
    
    def test_get_connectors(self):
        response = client.get("/connectors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

class TestSystem:
    """System endpoints"""
    
    def test_get_state(self):
        response = client.get("/state")
        assert response.status_code == 200

class TestLibrary:
    """Library endpoints"""
    
    def test_add_library_item(self):
        response = client.post(
            "/library/add",
            json={"title": "Test", "type": "Note", "content": "Content"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] == True

class TestArtifacts:
    """Artifact creation endpoints"""
    
    def test_create_markdown(self):
        response = client.post(
            "/artifact/create",
            json={"title": "Test", "content": "# Test", "format": "markdown"}
        )
        assert response.status_code == 200
    
    def test_create_csv(self):
        response = client.post(
            "/artifact/create",
            json={"title": "Test", "content": "col1,col2", "format": "csv"}
        )
        assert response.status_code == 200

class TestErrorHandling:
    """Error handling and validation"""
    
    def test_middleware_adds_request_id(self):
        """Test that middleware adds request ID"""
        response = client.get("/health")
        assert "x-request-id" in response.headers

class TestPerformance:
    """Performance tests"""
    
    def test_response_time_health(self):
        import time
        start = time.time()
        client.get("/health")
        elapsed = time.time() - start
        assert elapsed < 1.0
    
    def test_multiple_requests(self):
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
