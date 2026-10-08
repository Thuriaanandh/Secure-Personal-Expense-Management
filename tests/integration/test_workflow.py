from fastapi.testclient import TestClient


def test_complete_user_lifecycle_and_ledger_workflow(client: TestClient):
    # Step 1: Register new account
    reg_payload = {
        "email": "workflow_user@spema.internal",
        "username": "workflow_dev",
        "password": "ProductionP@ssw0rd2026!",
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]
    assert user_id > 0

    # Step 2: Login and receive JWT
    login_payload = {"email_or_username": "workflow_dev", "password": "ProductionP@ssw0rd2026!"}
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Verify /me profile
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "workflow_dev"

    # Step 4: Create Category
    cat_resp = client.post(
        "/api/v1/categories", headers=headers, json={"name": "Engineering Retainer", "type": "BOTH"}
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # Step 5: Record Income
    income_resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "amount": 5000.00,
            "type": "INCOME",
            "category_id": cat_id,
            "transaction_date": "2026-10-01",
            "description": "Monthly Retainer Payout",
        },
    )
    assert income_resp.status_code == 201
    income_id = income_resp.json()["id"]

    # Step 6: Record Expense
    expense_resp = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "amount": 1200.00,
            "type": "EXPENSE",
            "category_id": cat_id,
            "transaction_date": "2026-10-05",
            "description": "Server Hosting Costs",
        },
    )
    assert expense_resp.status_code == 201
    expense_id = expense_resp.json()["id"]

    # Step 7: View Monthly Summary
    summary_resp = client.get("/api/v1/reports/summary?year=2026&month=10", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert float(summary["total_income"]) == 5000.00
    assert float(summary["total_expenses"]) == 1200.00
    assert float(summary["net_savings"]) == 3800.00
    assert summary["transaction_count"] == 2

    # Step 8: Update Expense Transaction
    update_resp = client.put(
        f"/api/v1/transactions/{expense_id}",
        headers=headers,
        json={"amount": 1250.00, "description": "Server Hosting and CDN"},
    )
    assert update_resp.status_code == 200
    assert float(update_resp.json()["amount"]) == 1250.00

    # Step 9: Delete Income Transaction
    del_resp = client.delete(f"/api/v1/transactions/{income_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify income is deleted
    get_del_resp = client.get(f"/api/v1/transactions/{income_id}", headers=headers)
    assert get_del_resp.status_code == 404

    # Step 10: Logout and verify token is revoked
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Step 11: Attempt to use revoked token
    revoked_resp = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_resp.status_code == 401
