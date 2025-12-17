import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.middleware import RequestIdMiddleware, request_id_context

def test_request_id_middleware():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    def test_endpoint():
        # Verify context var is set within the request
        return {"request_id": request_id_context.get()}

    client = TestClient(app)

    # 1. Test auto-generation
    resp = client.get("/test")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    generated_id = resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == generated_id
    assert len(generated_id) > 10

    # 2. Test propagation
    explicit_id = "test-123"
    resp = client.get("/test", headers={"X-Request-ID": explicit_id})
    assert resp.headers["X-Request-ID"] == explicit_id
    assert resp.json()["request_id"] == explicit_id
