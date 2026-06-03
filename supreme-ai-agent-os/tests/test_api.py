"""
Supreme AI Agent OS - API Tests
Comprehensive test suite for all API endpoints
"""
import pytest
import json
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
        assert "search" in data
    
    def test_capabilities_structure(self):
        response = client.get("/capabilities")
        data = response.json()
        assert isinstance(data.get("llm"), dict)
        assert isinstance(data.get("connectors"), dict)

class TestAgents:
    """Agent endpoints"""
    
    def test_get_agents(self):
        response = client.get("/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_agent_run_minimal(self):
        """Test agent run with minimal input"""
        response = client.post(
            "/agent/run",
            json={
                "prompt": "Hello",
                "agent_id": "executive"
            }
        )
        assert response.status_code == 200
        assert "answer" in response.json() or "error" not in response.json()

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
        data = response.json()
        assert "library" in data or data.get("error") is None

class TestLibrary:
    """Library endpoints"""
    
    def test_add_library_item(self):
        response = client.post(
            "/library/add",
            json={
                "title": "Test Item",
                "type": "Note",
                "content": "Test content"
            }
        )
        assert response.status_code == 200
        assert response.json()["ok"] == True
        assert "item" in response.json()

class TestArtifacts:
    """Artifact creation endpoints"""
    
    def test_create_markdown(self):
        response = client.post(
            "/artifact/create",
            json={
                "title": "Test",
                "content": "# Test",
                "format": "markdown"
            }
        )
        assert response.status_code == 200
    
    def test_create_csv(self):
        response = client.post(
            "/artifact/create",
            json={
                "title": "Test",
                "content": "col1,col2\nval1,val2",
                "format": "csv"
            }
        )
        assert response.status_code == 200
    
    def test_create_html(self):
        response = client.post(
            "/artifact/create",
            json={
                "title": "Test",
                "content": "<p>Test</p>",
                "format": "html"
            }
        )
        assert response.status_code == 200

class TestErrorHandling:
    """Error handling and validation"""
    
    def test_invalid_request_body(self):
        """Test invalid JSON body"""
        response = client.post(
            "/agent/run",
            json={"invalid_field": "value"}
        )
        # Should either return 422 validation error or 500
        assert response.status_code >= 400
    
    def test_middleware_adds_request_id(self):
        """Test that middleware adds request ID"""
        response = client.get("/health")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

class TestPerformance:
    """Performance and resilience tests"""
    
    def test_response_time_health(self):
        """Health check should respond quickly"""
        import time
        start = time.time()
        client.get("/health")
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should respond within 1 second

    def test_multiple_requests(self):
        """Test handling multiple concurrent-like requests"""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
