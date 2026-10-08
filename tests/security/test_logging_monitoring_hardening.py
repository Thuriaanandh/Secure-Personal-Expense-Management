"""
Security Testing Suite for Logging, Monitoring, and Hardening (Phase 15).

Verifies:
1. Structured security logging with strict sensitive data redaction (CWE-532).
2. Operational and security metrics tracking in Prometheus and JSON formats.
3. HTTP security headers, HSTS, COOP, CORP, and request correlation IDs.
4. Metric counter increments on auth failure, authz/IDOR violations, and operations.
"""

from fastapi.testclient import TestClient

from src.app.core.logging import (
    clear_security_events_for_testing,
    get_recent_security_events,
    log_security_event,
    mask_security_payload,
)
from src.app.core.metrics import metrics


def test_structured_security_logging_redaction_and_event_format():
    """Verify log_security_event enforces strict redaction of sensitive credentials (CWE-532)."""
    clear_security_events_for_testing()

    raw_details = {
        "username": "alice",
        "password": "SuperSecretPassword123!",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy",
        "access_token": "sensitive_access_token_val",
        "secret": "top_secret_key",
        "authorization": "Bearer secret_bearer_token",
        "safe_field": "public_data",
        "nested": {
            "password_hash": "$argon2id$v=19$...",
            "cookie": "session=abc",
            "count": 42,
        },
    }

    # Verify masking function
    masked = mask_security_payload(raw_details)
    assert masked["password"] == "[REDACTED]"
    assert masked["token"] == "[REDACTED]"
    assert masked["access_token"] == "[REDACTED]"
    assert masked["secret"] == "[REDACTED]"
    assert masked["authorization"] == "[REDACTED]"
    assert masked["safe_field"] == "public_data"
    assert masked["nested"]["password_hash"] == "[REDACTED]"
    assert masked["nested"]["cookie"] == "[REDACTED]"
    assert masked["nested"]["count"] == 42

    # Emit event and verify buffer structure
    event = log_security_event(
        event_type="AUTH_TEST",
        action="TEST_ACTION",
        status_code=200,
        user_id=1,
        client_ip="127.0.0.1",
        correlation_id="corr-12345",
        resource="/api/v1/test",
        details=raw_details,
    )

    assert event["event_type"] == "AUTH_TEST"
    assert event["correlation_id"] == "corr-12345"
    assert event["details"]["password"] == "[REDACTED]"
    assert event["details"]["token"] == "[REDACTED]"

    events = get_recent_security_events(limit=10)
    assert len(events) >= 1
    assert events[-1]["event_type"] == "AUTH_TEST"


def test_prometheus_and_json_metrics_endpoints(client: TestClient):
    """Verify /metrics provides Prometheus exposition and /api/v1/metrics provides JSON."""
    # 1. Prometheus endpoint
    prom_resp = client.get("/metrics")
    assert prom_resp.status_code == 200
    assert "text/plain" in prom_resp.headers["content-type"]
    prom_text = prom_resp.text
    assert "spema_app_uptime_seconds" in prom_text
    assert "spema_auth_successes_total" in prom_text
    assert "spema_auth_failures_total" in prom_text
    assert "spema_authz_failures_total" in prom_text
    assert "spema_http_requests_total" in prom_text

    # 2. JSON metrics endpoint
    json_resp = client.get("/api/v1/metrics")
    assert json_resp.status_code == 200
    data = json_resp.json()
    assert data["status"] == "operational"
    assert "uptime_seconds" in data
    assert "counters" in data
    assert "auth_failures_total" in data["counters"]
    assert "authz_failures_total" in data["counters"]
    assert "transactions_created_total" in data["counters"]


def test_metrics_increments_on_auth_and_authz_events(client: TestClient):
    """Verify metrics accurately track authentication failures, successes, and IDOR events."""
    metrics.reset()

    # Register and login User A
    user_a_email = "metrics_user_a@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "username": "metrics_user_a", "password": "SecurePassword123!"},
    )

    # Failed login increments auth_failures_total
    client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user_a_email, "password": "WrongPassword999!"},
    )
    assert metrics.auth_failures_total >= 1

    # Successful login increments auth_successes_total
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user_a_email, "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    assert metrics.auth_successes_total >= 1
    token_a = login_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create category and transaction to increment transactions_created_total
    client.cookies.clear()
    cat_resp = client.post(
        "/api/v1/categories",
        headers=headers_a,
        json={"name": "General Expenses", "type": "BOTH"},
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    txn_resp = client.post(
        "/api/v1/transactions",
        headers=headers_a,
        json={"category_id": cat_id, "amount": "75.00", "type": "EXPENSE", "transaction_date": "2026-10-08"},
    )
    assert txn_resp.status_code == 201
    txn_id = txn_resp.json()["id"]
    assert metrics.transactions_created_total >= 1

    # Register User B
    user_b_email = "metrics_user_b@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "username": "metrics_user_b", "password": "SecurePassword123!"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": user_b_email, "password": "SecurePassword123!"},
    )
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempting IDOR on User A's transaction increments authz_failures_total
    client.cookies.clear()
    idor_resp = client.get(f"/api/v1/transactions/{txn_id}", headers=headers_b)
    assert idor_resp.status_code == 404
    assert metrics.authz_failures_total >= 1

    # Export report increments reports_generated_total
    client.cookies.clear()
    rep_resp = client.get("/api/v1/reports/export-json", headers=headers_a)
    assert rep_resp.status_code == 200
    assert metrics.reports_generated_total >= 1


def test_security_hardening_headers_and_correlation_id(client: TestClient):
    """Verify all OWASP hardening headers, HSTS, COOP, CORP, and X-Correlation-ID are present."""
    resp = client.get("/healthz")
    assert resp.status_code == 200

    headers = resp.headers
    # Correlation ID
    assert "X-Correlation-ID" in headers
    assert len(headers["X-Correlation-ID"]) > 10

    # OWASP Defense-in-Depth Headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers["Permissions-Policy"]
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"

    # HSTS
    assert "Strict-Transport-Security" in headers
    assert "max-age=" in headers["Strict-Transport-Security"]
    assert "includeSubDomains" in headers["Strict-Transport-Security"]

    # CSP
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
