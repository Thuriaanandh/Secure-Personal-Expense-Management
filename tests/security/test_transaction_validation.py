from fastapi.testclient import TestClient


def test_cannot_assign_incompatible_category_type_on_create(
    client: TestClient, auth_headers_user_a
):
    """
    REGRESSION TEST (Fix for CWE-840 / CWE-285 Integrity Violation):
    Cannot assign an EXPENSE transaction to an INCOME category (Category 1: Salary).
    """
    resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 500.00,
            "type": "EXPENSE",
            "category_id": 1,  # System Category 'Salary' is INCOME-only
            "transaction_date": "2026-10-08",
            "description": "Attempted Ledger Corruption",
        },
    )
    assert resp.status_code == 400
    assert "incompatible" in resp.json()["detail"].lower()


def test_cannot_assign_incompatible_category_type_on_update(
    client: TestClient, auth_headers_user_a
):
    """
    Verifies that updating a transaction to an incompatible category type is blocked.
    """
    # 1. Create valid Income transaction under Category 1 (Salary)
    create_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 3000.00,
            "type": "INCOME",
            "category_id": 1,
            "transaction_date": "2026-10-08",
            "description": "Legitimate Salary",
        },
    )
    assert create_resp.status_code == 201
    txn_id = create_resp.json()["id"]

    # 2. Attempt to update category to Category 5 (Groceries & Food, which is EXPENSE-only)
    update_resp = client.put(
        f"/api/v1/transactions/{txn_id}",
        headers=auth_headers_user_a,
        json={
            "category_id": 5  # EXPENSE-only category
        },
    )
    assert update_resp.status_code == 400
    assert "incompatible" in update_resp.json()["detail"].lower()


def test_both_category_type_accepts_either_income_or_expense(
    client: TestClient, auth_headers_user_a
):
    """
    Verifies that a custom category with type 'BOTH' accepts both INCOME and EXPENSE transactions.
    """
    # Create custom category with type 'BOTH'
    cat_resp = client.post(
        "/api/v1/categories",
        headers=auth_headers_user_a,
        json={"name": "Flexible Contracts", "type": "BOTH"},
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # Create INCOME with this category -> Must succeed
    inc_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 1000.00,
            "type": "INCOME",
            "category_id": cat_id,
            "transaction_date": "2026-10-08",
            "description": "Contract Inbound",
        },
    )
    assert inc_resp.status_code == 201

    # Create EXPENSE with this category -> Must succeed
    exp_resp = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 250.00,
            "type": "EXPENSE",
            "category_id": cat_id,
            "transaction_date": "2026-10-08",
            "description": "Contract Expense",
        },
    )
    assert exp_resp.status_code == 201


def test_date_range_validation_rejects_inverted_dates(client: TestClient, auth_headers_user_a):
    """
    REGRESSION TEST (Fix for CWE-20 / CWE-400 Date Range Validation):
    Rejects query where start_date > end_date.
    """
    resp = client.get(
        "/api/v1/transactions?start_date=2026-12-31&end_date=2026-01-01",
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 400
    assert "cannot be later than" in resp.json()["detail"].lower()


def test_date_range_validation_rejects_excessive_span(client: TestClient, auth_headers_user_a):
    """
    REGRESSION TEST (SEC-017 / CWE-400 Memory Exhaustion DoS Prevention):
    Rejects date range query exceeding 5 years (1826 days).
    """
    resp = client.get(
        "/api/v1/transactions?start_date=2020-01-01&end_date=2026-01-01",
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 400
    assert "cannot exceed 5 years" in resp.json()["detail"].lower()


def test_date_filtering_returns_transactions_within_window(client: TestClient, auth_headers_user_a):
    """
    Verifies that date filter parameters correctly return records matching the date boundary.
    """
    # Create txn in Oct 2026
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 100.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-15",
            "description": "Mid-October Grocery",
        },
    )
    # Create txn in Nov 2026
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 200.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-11-15",
            "description": "Mid-November Grocery",
        },
    )

    # Query strictly Oct 2026
    resp = client.get(
        "/api/v1/transactions?start_date=2026-10-01&end_date=2026-10-31",
        headers=auth_headers_user_a,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["description"] == "Mid-October Grocery"
