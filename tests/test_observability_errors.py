import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from backend.main import app

def test_exception_handler_json_format():
    """Verify that exceptions return the standard JSON error format."""
    client = TestClient(app)
    
    # 1. Test 404 (StarletteHTTPException)
    resp = client.get("/api/non-existent-route")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "correlation_id" in data["error"]

    # 2. Test RequestValidationError (implicitly via invalid request)
    # Sending invalid data to an endpoint
    resp = client.post("/api/auth/register", json={}) # Missing fields
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
