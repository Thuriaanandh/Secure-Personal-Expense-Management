"""System and API endpoint testing suite verifying OpenAPI schemas, health probes, and UI routes."""

from fastapi.testclient import TestClient


def test_system_healthz_and_readyz_probes(client: TestClient):
    """Verify system liveness (/healthz) and readiness (/readyz) probes."""
    resp_health = client.get("/healthz")
    assert resp_health.status_code == 200
    data_h = resp_health.json()
    assert data_h["status"] == "healthy"
    assert "Secure Personal Expense Management Application" in data_h["service"]

    resp_ready = client.get("/readyz")
    assert resp_ready.status_code == 200
    data_r = resp_ready.json()
    assert data_r["status"] == "ready"


def test_openapi_specification_schema(client: TestClient):
    """Verify OpenAPI JSON schema definition is valid and lists all protected routes."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema
    assert "/api/v1/transactions" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/reports/summary" in schema["paths"]


def test_owasp_security_headers_enforced(client: TestClient):
    """Verify mandatory OWASP security headers are attached to API and static responses."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "default-src 'self'" in headers.get("content-security-policy", "")
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_web_ui_routes_accessible(client: TestClient):
    """Verify HTML front-end navigation routes render successfully."""
    # Landing / Login page
    resp_login = client.get("/login")
    assert resp_login.status_code == 200
    assert "text/html" in resp_login.headers.get("content-type", "")
    assert "SPEMA" in resp_login.text
    assert "Welcome Back" in resp_login.text

    # Registration page
    resp_reg = client.get("/register")
    assert resp_reg.status_code == 200
    assert "text/html" in resp_reg.headers.get("content-type", "")
