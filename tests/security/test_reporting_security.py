from fastapi.testclient import TestClient


def test_csv_export_scopes_to_user_only(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # User A records a transaction
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 1234.56,
            "type": "INCOME",
            "category_id": 1,
            "transaction_date": "2026-10-08",
            "description": "UserAPrivateAuditIncome",
        },
    )

    # User B exports CSV
    resp_b = client.get("/api/v1/reports/export-csv", headers=auth_headers_user_b)
    assert resp_b.status_code == 200
    csv_text_b = resp_b.text
    assert "UserAPrivateAuditIncome" not in csv_text_b
    assert "1234.56" not in csv_text_b

    # User A exports CSV
    resp_a = client.get("/api/v1/reports/export-csv", headers=auth_headers_user_a)
    assert resp_a.status_code == 200
    csv_text_a = resp_a.text
    assert "UserAPrivateAuditIncome" in csv_text_a
    assert "1234.56" in csv_text_a


def test_csv_export_neutralizes_formula_injection(client: TestClient, auth_headers_user_a):
    # User A saves transaction with formula injection payloads (CWE-1236)
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 10.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": "=SUM(A1:A100)",
        },
    )
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 20.00,
            "type": "EXPENSE",
            "category_id": 5,
            "transaction_date": "2026-10-08",
            "description": '@HYPERLINK("http://malicious.site")',
        },
    )

    resp = client.get("/api/v1/reports/export-csv", headers=auth_headers_user_a)
    assert resp.status_code == 200
    csv_content = resp.text

    # Formulas must be escaped with prepended single quote (')
    assert "'=SUM(A1:A100)" in csv_content
    assert "'@HYPERLINK(" in csv_content
    # Raw unescaped formula must not appear at the start of a quoted field
    assert '"=SUM' not in csv_content
    assert '"@HYPERLINK' not in csv_content


def test_json_export_scopes_to_user_only(
    client: TestClient, auth_headers_user_a, auth_headers_user_b
):
    # User A records a transaction
    client.post(
        "/api/v1/transactions",
        headers=auth_headers_user_a,
        json={
            "amount": 888.88,
            "type": "INCOME",
            "category_id": 1,
            "transaction_date": "2026-10-08",
            "description": "UserAJsonAuditRecord",
        },
    )

    # User B requests JSON report
    resp_b = client.get("/api/v1/reports/export-json", headers=auth_headers_user_b)
    assert resp_b.status_code == 200
    items_b = resp_b.json()
    assert all(item["description"] != "UserAJsonAuditRecord" for item in items_b)

    # User A requests JSON report
    resp_a = client.get("/api/v1/reports/export-json", headers=auth_headers_user_a)
    assert resp_a.status_code == 200
    items_a = resp_a.json()
    assert any(item["description"] == "UserAJsonAuditRecord" for item in items_a)


def test_report_export_date_validation_regression(client: TestClient, auth_headers_user_a):
    """
    REGRESSION TEST FOR DEFECT 2:
    Verify inverted date ranges (start_date > end_date) return HTTP 400 Bad Request
    rather than unhandled HTTP 500 Internal Server Error.
    """
    # 1. Test CSV export with inverted date range
    resp_csv = client.get(
        "/api/v1/reports/export-csv?start_date=2026-12-31&end_date=2026-01-01",
        headers=auth_headers_user_a,
    )
    assert resp_csv.status_code == 400
    assert "start_date cannot be later than end_date" in resp_csv.json()["detail"]

    # 2. Test JSON export with inverted date range
    resp_json = client.get(
        "/api/v1/reports/export-json?start_date=2026-12-31&end_date=2026-01-01",
        headers=auth_headers_user_a,
    )
    assert resp_json.status_code == 400
    assert "start_date cannot be later than end_date" in resp_json.json()["detail"]

