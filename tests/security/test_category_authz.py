from fastapi.testclient import TestClient


def test_cannot_modify_or_delete_system_categories(client: TestClient, auth_headers_user_a):
    """
    REGRESSION TEST (Fix for CWE-285):
    System categories (is_system=True) must be immutable and cannot be deleted or modified.
    """
    # Attempt to rename System Category 1 (Salary)
    put_resp = client.put(
        "/api/v1/categories/1", headers=auth_headers_user_a, json={"name": "Hacked Salary"}
    )
    assert put_resp.status_code == 403
    assert "system categories cannot be modified" in put_resp.json()["detail"].lower()

    # Attempt to delete System Category 1
    del_resp = client.delete("/api/v1/categories/1", headers=auth_headers_user_a)
    assert del_resp.status_code == 403
    assert "system categories cannot be deleted" in del_resp.json()["detail"].lower()


def test_cannot_modify_or_delete_other_user_category(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    """
    REGRESSION TEST (Fix for CWE-639 / BOLA):
    User B cannot update or delete User A's custom category (uniform 404 anti-enumeration).
    """
    # 1. User A creates custom category
    create_resp = client.post(
        "/api/v1/categories",
        headers=auth_headers_user_a,
        json={"name": "Alice Private Retainer", "type": "INCOME"},
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["id"]

    # 2. User B attempts to rename User A's category
    put_resp = client.put(
        f"/api/v1/categories/{cat_id}",
        headers=auth_headers_user_b,
        json={"name": "Tampered By Bob"},
    )
    assert put_resp.status_code == 404

    # 3. User B attempts to delete User A's category
    del_resp = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers_user_b)
    assert del_resp.status_code == 404

    # 4. Verify User A's category remains intact
    cats_resp = client.get("/api/v1/categories", headers=auth_headers_user_a)
    assert any(c["name"] == "Alice Private Retainer" for c in cats_resp.json())


def test_cannot_delete_category_with_active_transactions(client: TestClient, auth_headers_user_a):
    """
    REGRESSION TEST (Fix for CWE-400 / Data Integrity Violation):
    Cannot delete a category that has transactions referencing it.
    """
    # 1. User A creates custom category
    create_resp = client.post(
        "/api/v1/categories",
        headers=auth_headers_user_a,
        json={"name": "Active Contract", "type": "EXPENSE"},
    )
    cat_id = create_resp.json()["id"]

    # 2. User A creates transaction using this category
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 200.00,
            "type": "EXPENSE",
            "category_id": cat_id,
            "transaction_date": "2026-10-08",
            "description": "Equipment Purchase",
        },
    )

    # 3. User A attempts to delete the category
    del_resp = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers_user_a)
    assert del_resp.status_code == 400
    assert "associated transactions" in del_resp.json()["detail"].lower()


def test_can_update_and_delete_empty_custom_category(client: TestClient, auth_headers_user_a):
    """
    Verifies full lifecycle of custom categories (create, update, delete).
    """
    # Create
    create_resp = client.post(
        "/api/v1/categories",
        headers=auth_headers_user_a,
        json={"name": "Temporary Project", "type": "EXPENSE"},
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["id"]

    # Update
    put_resp = client.put(
        f"/api/v1/categories/{cat_id}",
        headers=auth_headers_user_a,
        json={"name": "Renamed Project"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Renamed Project"

    # Delete
    del_resp = client.delete(f"/api/v1/categories/{cat_id}", headers=auth_headers_user_a)
    assert del_resp.status_code == 200
