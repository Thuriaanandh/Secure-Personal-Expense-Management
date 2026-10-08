import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://192.168.49.2:30080"

def test_k8s_service():
    print(f"[*] Testing SPEMA Kubernetes Service at {BASE_URL}...")
    
    # 1. Healthcheck
    req = urllib.request.Request(f"{BASE_URL}/healthz")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        print(f"[+] Healthcheck passed: {data}")

    # 2. User Registration
    user_payload = {
        "email": "k8s_test_user@example.com",
        "username": "k8s_tester",
        "password": "SecurePassword123!"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/register",
        data=json.dumps(user_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            reg_data = json.loads(resp.read().decode())
            print(f"[+] User registration succeeded: user_id={reg_data['id']}, email={reg_data['email']}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print("[*] User already registered, continuing to login...")
        else:
            raise

    # 3. User Login
    login_payload = {
        "email_or_username": "k8s_test_user@example.com",
        "password": "SecurePassword123!"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=json.dumps(login_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        login_data = json.loads(resp.read().decode())
        token = login_data["access_token"]
        print(f"[+] User login succeeded, JWT token obtained (length {len(token)})")

    # 4. Fetch System Categories
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{BASE_URL}/api/v1/categories", headers=headers)
    with urllib.request.urlopen(req) as resp:
        categories = json.loads(resp.read().decode())
        print(f"[+] Categories retrieved: {len(categories)} categories found.")
        salary_cat = next(c for c in categories if c["name"] == "Salary")
        print(f"    Selected Category: id={salary_cat['id']}, name={salary_cat['name']}")

    # 5. Create Transaction
    tx_payload = {
        "amount": 4500.00,
        "type": "INCOME",
        "category_id": salary_cat["id"],
        "transaction_date": "2026-10-08",
        "description": "Monthly Kubernetes verified salary"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/transactions",
        data=json.dumps(tx_payload).encode("utf-8"),
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        tx_data = json.loads(resp.read().decode())
        print(f"[+] Transaction created successfully: id={tx_data['id']}, amount={tx_data['amount']}")

    # 6. Fetch Financial Summary Report
    req = urllib.request.Request(f"{BASE_URL}/api/v1/reports/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        summary_data = json.loads(resp.read().decode())
        print(f"[+] Summary report retrieved: total_income={summary_data['total_income']}, net_savings={summary_data['net_savings']}")
        assert float(summary_data["total_income"]) >= 4500.00

    print("\n[SUCCESS] Complete Kubernetes Deployment & API Workflow Verified Successfully!")

if __name__ == "__main__":
    test_k8s_service()
