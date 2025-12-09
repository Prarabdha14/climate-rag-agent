# tests/test_api.py
from fastapi.testclient import TestClient
import sys
import os

# Add src to path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from api.app import app

client = TestClient(app)

def test_health_check():
    """Test if the API is running and retriever is ready."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_query_endpoint():
    """Test the search functionality."""
    # Note: This assumes you have data indexed.
    payload = {"query": "climate change", "k": 3}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)

def test_invalid_query():
    """Test error handling for missing query."""
    response = client.post("/query", json={})
    # Should handle gracefully (return empty results or error detail)
    assert "results" in response.json() or "detail" in response.json()

def test_demo_outputs():
    """Test if demo outputs endpoint works."""
    response = client.get("/demo-outputs")
    assert response.status_code == 200
    assert "outputs" in response.json()