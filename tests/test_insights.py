import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_llm_client
from app.clients.mock_llm import MockLLMClient
from app.utils.rate_limiter import limiter

# Override LLM client with mock for testing
def get_mock_llm_client():
    return MockLLMClient()

app.dependency_overrides[get_llm_client] = get_mock_llm_client

# CRITICAL FIX: Disable rate limiting for tests
app.state.limiter = None  # This disables the rate limiter

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_generate_insight_valid_request():
    """Test successful insight generation"""
    payload = {
        "user_id": "test_user_123",
        "tenant_id": "test_tenant",
        "input_type": "metrics",
        "data": {
            "metric_name": "sales_data",
            "values": [100, 105, 103, 150],
            "timestamps": [
                "2024-12-10T00:00:00Z",
                "2024-12-11T00:00:00Z",
                "2024-12-12T00:00:00Z",
                "2024-12-13T00:00:00Z"
            ]
        }
    }

    response = client.post("/api/v1/generate-insight", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["tenant_id"] == "test_tenant"
    assert "features" in data
    assert "insight" in data
    assert data["features"]["severity"] in ["critical", "high", "medium", "low"]
    assert len(data["insight"]["recommended_actions"]) > 0


def test_generate_insight_insufficient_data():
    """Test validation with insufficient data points"""
    payload = {
        "user_id": "test_user_123",
        "tenant_id": "test_tenant",
        "input_type": "metrics",
        "data": {
            "metric_name": "sales_data",
            "values": [100]  # Only 1 value - should fail
        }
    }

    response = client.post("/api/v1/generate-insight", json=payload)
    assert response.status_code == 422  # Validation error


def test_generate_insight_missing_fields():
    """Test validation with missing required fields"""
    payload = {
        "user_id": "test_user_123",
        # Missing tenant_id
        "input_type": "metrics",
        "data": {
            "metric_name": "sales_data",
            "values": [100, 150]
        }
    }

    response = client.post("/api/v1/generate-insight", json=payload)
    assert response.status_code == 422


def test_insight_history_endpoint():
    """Test insight history retrieval"""
    response = client.get(
        "/api/v1/insight-history/test_user_123?tenant_id=test_tenant"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["tenant_id"] == "test_tenant"
    assert "insights" in data
    assert "pagination" in data


def test_mock_llm_endpoint():
    """Test mock LLM endpoint"""
    payload = {
        "prompt": "Test prompt",
        "temperature": 0.7,
        "max_tokens": 500
    }

    response = client.post("/api/v1/mock-llm", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "content" in data
    assert "model" in data
    assert "usage" in data