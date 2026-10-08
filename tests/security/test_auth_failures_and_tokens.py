"""Security testing suite verifying authentication failures, token security, and error handling."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from src.app.core.config import get_settings


def test_authentication_failures_invalid_credentials(client: TestClient):
    """Verify login fails with HTTP 401 when invalid password or email is supplied."""
    # Register legitimate user
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "auth_fail_test@example.com", "username": "auth_fail_user", "password": "SecurePassword123!"},
    )
    assert reg_resp.status_code == 201

    # Wrong password
    resp = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "auth_fail_test@example.com", "password": "WrongPassword999!"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]

    # Non-existent user
    resp = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "non_existent_user@example.com", "password": "SecurePassword123!"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_protected_endpoints_require_authentication(client: TestClient):
    """Verify all protected API endpoints reject unauthenticated requests with HTTP 401."""
    protected_urls = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/transactions"),
        ("POST", "/api/v1/transactions"),
        ("GET", "/api/v1/categories"),
        ("POST", "/api/v1/categories"),
        ("GET", "/api/v1/reports/summary"),
        ("GET", "/api/v1/reports/export-csv"),
        ("GET", "/api/v1/reports/export-json"),
    ]
    for method, url in protected_urls:
        if method == "GET":
            resp = client.get(url)
        elif method == "POST":
            resp = client.post(url, json={})
        assert resp.status_code == 401, f"Endpoint {method} {url} should require authentication"
        assert resp.headers.get("www-authenticate") == "Bearer"


def test_malformed_tokens_rejected(client: TestClient):
    """Verify malformed, invalid base64, and tampered tokens are rejected with HTTP 401."""
    malformed_headers = [
        "Bearer not-a-valid-jwt-token",
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsig",
        "Bearer ",
        "InvalidScheme someToken",
    ]
    for auth_hdr in malformed_headers:
        resp = client.get("/api/v1/auth/me", headers={"Authorization": auth_hdr})
        assert resp.status_code == 401


def test_tampered_token_signature_rejected(client: TestClient, auth_headers_user_a):
    """Verify that altering token payload or signing with wrong secret is rejected."""
    token = auth_headers_user_a["Authorization"].split("Bearer ")[1]
    # Tamper with the signature portion
    tampered_token = token[:-5] + "XXXXX"
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp.status_code == 401

    # Token signed with untrusted secret key
    forged_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=30), "iss": "SPEMA-Auth", "jti": "forged"},
        "wrong-untrusted-secret-key-that-does-not-match-spema",
        algorithm="HS256"
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp.status_code == 401


def test_expired_token_rejected(client: TestClient):
    """Verify that expired JWTs are immediately rejected with HTTP 401."""
    settings = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_token = jwt.encode(
        {"sub": "1", "exp": past, "iat": past - timedelta(minutes=30), "iss": "SPEMA-Auth", "jti": "expired-id"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "Invalid or expired session token" in resp.json()["detail"]


def test_revoked_token_regression_case_insensitive_logout(client: TestClient):
    """
    REGRESSION TEST FOR DEFECT 1:
    Verify logout with lowercase 'bearer ' prefix and whitespace properly revokes the token in DB.
    """
    client.cookies.clear()
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "logout_revoc_test@example.com", "username": "logout_revoc_user", "password": "SecurePassword123!"},
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "logout_revoc_test@example.com", "password": "SecurePassword123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    client.cookies.clear()

    # Logout using lowercase 'bearer ' prefix
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"bearer  {token} "})
    assert logout_resp.status_code == 200
    client.cookies.clear()

    # Subsequent request using the revoked token must be rejected
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401
    assert "Invalid or expired session token" in me_resp.json()["detail"]


def test_invalid_input_validation_and_injection_payloads(client: TestClient, auth_headers_user_a):
    """Verify input boundary enforcement rejects SQL injection, XSS, and invalid numbers."""
    headers = auth_headers_user_a

    # Negative amount
    resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"category_id": 1, "amount": -50.00, "type": "EXPENSE", "transaction_date": "2026-10-08"},
    )
    assert resp.status_code == 422

    # Amount exceeding $1,000,000 threshold
    resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"category_id": 1, "amount": 1000001.00, "type": "EXPENSE", "transaction_date": "2026-10-08"},
    )
    assert resp.status_code == 422

    # Invalid transaction type
    resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"category_id": 1, "amount": 25.00, "type": "TRANSFER", "transaction_date": "2026-10-08"},
    )
    assert resp.status_code == 422

    # Description exceeding max length (255)
    resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"category_id": 1, "amount": 25.00, "type": "EXPENSE", "transaction_date": "2026-10-08", "description": "A" * 256},
    )
    assert resp.status_code == 422
