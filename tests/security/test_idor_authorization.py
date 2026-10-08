from fastapi.testclient import TestClient


def test_cannot_read_other_user_transaction(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # 1. User A creates a transaction
    create_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 2500.00,
            "type": "INCOME",
            "category_id": 1,
            "transaction_date": "2026-10-08",
            "description": "User A Private Retainer",
        },
    )
    assert create_resp.status_code == 201
    txn_a_id = create_resp.json()["id"]

    # 2. User B attempts to access User A's transaction directly (IDOR / BOLA attack)
    idor_resp = client.get(f"/api/v1/transactions/{txn_a_id}", headers=auth_headers_user_b)
    # Must return 404 (Anti-Enumeration Defense: SEC-006)
    assert idor_resp.status_code == 404
    assert "not found" in idor_resp.json()["detail"].lower()


def test_cannot_update_other_user_transaction(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # 1. User A creates transaction
    create_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 150.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": "User A Legitimate Expense",
        },
    )
    assert create_resp.status_code == 201
    txn_a_id = create_resp.json()["id"]

    # 2. User B attempts to tamper with User A's transaction amount
    tamper_resp = client.put(
        f"/api/v1/transactions/{txn_a_id}",
        headers=auth_headers_user_b,
        json={"amount": 99999.00, "description": "Tampered By User B"},
    )
    # Must return 404
    assert tamper_resp.status_code == 404

    # 3. Verify original transaction remains unaltered when inspected by User A
    verify_resp = client.get(f"/api/v1/transactions/{txn_a_id}", headers=auth_headers_user_a)
    assert verify_resp.status_code == 200
    assert float(verify_resp.json()["amount"]) == 150.00
    assert verify_resp.json()["description"] == "User A Legitimate Expense"


def test_cannot_delete_other_user_transaction(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # 1. User A creates transaction
    create_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 300.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": "User A Sensitive Bill",
        },
    )
    assert create_resp.status_code == 201
    txn_a_id = create_resp.json()["id"]

    # 2. User B attempts to delete User A's transaction
    delete_resp = client.delete(f"/api/v1/transactions/{txn_a_id}", headers=auth_headers_user_b)
    # Must return 404
    assert delete_resp.status_code == 404

    # 3. Verify record still exists for User A
    verify_resp = client.get(f"/api/v1/transactions/{txn_a_id}", headers=auth_headers_user_a)
    assert verify_resp.status_code == 200


def test_cannot_search_or_list_other_user_transactions(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # User A creates transaction with specific search keyword
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 750.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": "ConfidentialMedicalTreatment",
        },
    )

    # User B queries transactions searching for that keyword
    search_resp = client.get(
        "/api/v1/transactions?keyword=ConfidentialMedicalTreatment", headers=auth_headers_user_b
    )
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert len(data) == 0


def test_cannot_aggregate_other_user_financials(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # User A records $10,000 income
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 10000.00,
            "type": "INCOME",
            "category_id": 1,
            "transaction_date": "2026-10-08",
            "description": "High Value Consulting",
        },
    )

    # User B checks monthly summary overview
    summary_resp = client.get(
        "/api/v1/reports/summary?year=2026&month=10", headers=auth_headers_user_b
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    # User B summary must NOT include User A's $10,000
    assert float(data["total_income"]) == 0.0


def test_reject_client_supplied_user_id(client: TestClient, auth_headers_user_a):
    # Attacker tries to inject user_id parameter in payload
    resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 100.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": "Tamper Attempt",
            "user_id": 9999,
        },
    )
    # Pydantic extra='forbid' must reject extra fields with 422
    assert resp.status_code == 422
    assert "extra_forbidden" in str(resp.json()) or "Extra inputs are not permitted" in str(
        resp.json()
    )


def test_unauthenticated_requests_rejected(client: TestClient):
    resp = client.get("/api/v1/transactions")
    assert resp.status_code == 401
