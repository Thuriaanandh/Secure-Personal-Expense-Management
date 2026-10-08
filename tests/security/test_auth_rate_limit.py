from fastapi.testclient import TestClient


def test_successful_logins_do_not_trigger_lockout_dos(client: TestClient):
    """
    REGRESSION TEST (Fix for CWE-400 Account Lockout DoS):
    Legitimate users logging in repeatedly must not be blocked by the rate limiter.
    """
    user_payload = {
        "email": "rate_user@spema.internal",
        "username": "rate_user",
        "password": "ValidPassword123!",
    }
    client.post("/api/v1/auth/register", json=user_payload)

    login_payload = {"email_or_username": "rate_user", "password": "ValidPassword123!"}

    # Execute 6 consecutive successful logins (exceeding default limit of 5 attempts)
    for _ in range(6):
        resp = client.post("/api/v1/auth/login", json=login_payload)
        assert resp.status_code == 200
        assert "access_token" in resp.json()


def test_consecutive_failed_logins_trigger_rate_limit(client: TestClient):
    """
    Verifies that malicious or repeated failed attempts trigger HTTP 429 Too Many Requests.
    """
    user_payload = {
        "email": "victim@spema.internal",
        "username": "victim_user",
        "password": "VictimPassword123!",
    }
    client.post("/api/v1/auth/register", json=user_payload)

    bad_login_payload = {"email_or_username": "victim_user", "password": "WrongPassword123!"}

    # First 5 failed attempts return 401 Unauthorized
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json=bad_login_payload)
        assert resp.status_code == 401

    # 6th attempt must be rejected with 429 Too Many Requests
    blocked_resp = client.post("/api/v1/auth/login", json=bad_login_payload)
    assert blocked_resp.status_code == 429
    assert "too many authentication attempts" in blocked_resp.json()["detail"].lower()


def test_successful_login_clears_previous_failed_attempts(client: TestClient):
    """
    Verifies that a successful login resets the failure counter.
    """
    user_payload = {
        "email": "reset_user@spema.internal",
        "username": "reset_user",
        "password": "CorrectPassword123!",
    }
    client.post("/api/v1/auth/register", json=user_payload)

    # 4 failed attempts
    for _ in range(4):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email_or_username": "reset_user", "password": "WrongPassword123!"},
        )
        assert resp.status_code == 401

    # 5th attempt succeeds
    good_resp = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "reset_user", "password": "CorrectPassword123!"},
    )
    assert good_resp.status_code == 200

    # Next attempt succeeds without hitting 429 because counter was reset
    next_good_resp = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "reset_user", "password": "CorrectPassword123!"},
    )
    assert next_good_resp.status_code == 200
