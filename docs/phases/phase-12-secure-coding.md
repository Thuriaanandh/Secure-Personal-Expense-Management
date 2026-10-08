# Phase 12: Secure Coding and Refactoring

**Project:** Secure Personal Expense Management Application (SPEMA)  
**Curriculum:** 24CYS401 Secure Software Engineering Laboratory  
**Document Version:** 1.1.0  
**Status:** Approved & Implemented  
**Release Tag:** `v1.1.0`  

---

## 1. Executive Summary & Objectives

Phase 12 transitions the baseline environment established in Phase 11 into a fully realized, hardened application implementation. This phase operationalizes all architectural, data modeling, threat modeling, and defensive security specifications designed across Phases 1 through 10.

### 1.1 Primary Security Mandate Enforcement

> **"An authenticated user must not be able to access, modify, search, aggregate, or report on another user's financial records."**

To maintain this absolute security invariant, Phase 12 enforces:
1. **Server-Derived Identity Only:** Client-supplied user identifiers (e.g., in request bodies, query strings, headers, or URL paths) are strictly rejected or ignored. The active tenant identity is derived solely from the cryptographically verified JWT bearer token via FastAPI's dependency injection (`Depends(get_current_active_user)`).
2. **Compound Tenancy Query Scoping:** All persistence repository queries explicitly incorporate `user_id` as part of the filtering criteria (e.g., `WHERE id = :id AND user_id = :uid`).
3. **Anti-Enumeration Responses (CWE-200 / SEC-006):** Inquiries for entities owned by another user or non-existent entities return identical `HTTP 404 Not Found` errors rather than `HTTP 403 Forbidden`, preventing resource ID enumeration.
4. **Defensive Data Sealing:** All incoming request DTOs enforce Pydantic v2 `model_config = {"extra": "forbid"}` to prevent parameter pollution and mass assignment attacks.

---

## 2. Security & Quality Weakness Remediation

In accordance with Phase 12 requirements, four real security and quality weaknesses were identified in the pre-refactored codebase, formally analyzed, remedied at the code level, and validated with regression tests.

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE 12 REMEDIATION OVERVIEW                                    |
+-------------------+-----------------------------+-----------------------+--------------------------+
| Weakness ID       | Classification              | Affected Component    | Regression Test Suite    |
+-------------------+-----------------------------+-----------------------+--------------------------+
| SPEMA-SEC-W01     | CWE-400 / DoS Lockout       | routers/auth.py       | test_auth_rate_limit.py  |
| SPEMA-SEC-W02     | CWE-840 / Integrity Flaw    | services/transaction  | test_transaction_val...  |
| SPEMA-SEC-W03     | CWE-20 / Resource Abuse     | schemas/transaction   | test_transaction_val...  |
| SPEMA-SEC-W04     | CWE-285 / SEC-006 BOLA      | routers/categories    | test_category_authz.py   |
+-------------------+-----------------------------+-----------------------+--------------------------+
```

---

### 2.1 Weakness 1: Unintended Account Lockout Denial-of-Service via Premature Rate Limiter Increment (CWE-400 / SEC-003)

#### A. Problem Description & Root Cause
The initial rate limiting implementation in `src/app/routers/auth.py` invoked `is_rate_limited(client_ip)` which automatically incremented the sliding-window attempt counter *prior* to authenticating the user's credentials. Furthermore, the counter was never cleared upon a successful login.

#### B. Security Impact
A legitimate user who logged in multiple times (e.g., switching devices, refreshing sessions, or accessing multiple API clients) would hit the threshold (5 attempts per minute) and be locked out with `HTTP 429 Too Many Requests`, even though all credentials were valid. This introduced a self-inflicted Denial-of-Service (DoS) condition on legitimate user accounts.

#### C. Code Fix & Refactoring
1. Refactored `src/app/core/rate_limit.py` to support inspection (`increment=False`) before authentication.
2. Modified `src/app/routers/auth.py` so that rate limit counters are only incremented upon *failed* authentication attempts.
3. Added an explicit call to `reset_rate_limit(key)` upon successful authentication, immediately restoring the user's rate window.

```python
# Fixed src/app/routers/auth.py
# 1. Check if already limited without incrementing
if is_rate_limited(rate_limit_key, max_attempts=5, window_seconds=60, increment=False):
    raise HTTPException(status_code=429, detail="Too many failed login attempts...")

user = auth_service.authenticate_user(db, form_data.username, form_data.password)
if not user:
    # 2. Only increment on failed attempt
    is_rate_limited(rate_limit_key, max_attempts=5, window_seconds=60, increment=True)
    raise HTTPException(status_code=401, detail="Invalid email or password.")

# 3. Clear rate limit on successful authentication
reset_rate_limit(rate_limit_key)
```

#### D. Regression Verification
Created `tests/security/test_auth_rate_limit.py`:
- `test_successful_logins_do_not_trigger_lockout_dos`: Verified that 6 consecutive valid logins complete successfully without triggering HTTP 429.
- `test_consecutive_failed_logins_trigger_rate_limit`: Verified that 5 failed attempts trigger HTTP 429 on the 6th attempt.
- `test_successful_login_clears_previous_failed_attempts`: Verified that failed attempts are reset upon a valid login.

---

### 2.2 Weakness 2: Ledger Integrity Corruption via Category Type Mismatch (CWE-840 / CWE-285)

#### A. Problem Description & Root Cause
Transactions in SPEMA are either `INCOME` or `EXPENSE`. Categories also define allowed transaction types (`INCOME`, `EXPENSE`, or `BOTH`). In the baseline code, `TransactionService.create_transaction` and `TransactionService.update_transaction` validated that the category existed and belonged to the user (or was a system category), but never verified that the `transaction.type` matched the `category.type`.

#### B. Security Impact
A user could log an `EXPENSE` (e.g., $5,000 for luxury goods) classified under the `Salary` category (which is strictly `INCOME`). This corrupted financial aggregation calculations, monthly summaries, budget tracking, and tax export reports, compromising ledger data integrity (CWE-840).

#### C. Code Fix & Refactoring
Enforced strict category compatibility checks in `src/app/services/transaction_service.py` during both creation and update phases:

```python
# Fixed src/app/services/transaction_service.py
if category.type != "BOTH" and category.type != transaction_in.type:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Category '{category.name}' only supports '{category.type}' transactions, not '{transaction_in.type}'.",
    )
```

#### D. Regression Verification
Added in `tests/security/test_transaction_validation.py`:
- `test_cannot_assign_incompatible_category_type_on_create`: Verified assigning an `EXPENSE` transaction to an `INCOME` category is rejected with HTTP 400.
- `test_cannot_assign_incompatible_category_type_on_update`: Verified updating an existing transaction to an incompatible category is rejected with HTTP 400.
- `test_both_category_type_accepts_either_income_or_expense`: Verified categories with type `BOTH` successfully accept both income and expense entries.

---

### 2.3 Weakness 3: Query Parameter Boundary Validation & Resource Exhaustion (CWE-20 / CWE-400 / SEC-017)

#### A. Problem Description & Root Cause
The `GET /api/v1/transactions` endpoint accepted optional `start_date` and `end_date` parameters, but lacked schema-level boundary enforcement. A client could submit:
1. Inverted date ranges where `start_date > end_date`.
2. Absurdly large spans (e.g., spanning 100 years), causing excessive database query load and denial of service.

#### B. Security Impact
Inverted dates produce empty or undefined query behaviors. Oversized date spans bypass anticipated paging constraints, causing high CPU/memory utilization on database servers when processing large ledgers.

#### C. Code Fix & Refactoring
Implemented Pydantic v2 `@model_validator(mode="after")` on `TransactionFilter` in `src/app/schemas/transaction.py`:

```python
# Fixed src/app/schemas/transaction.py
class TransactionFilter(BaseModel):
    # ... fields ...
    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date.")
            if (self.end_date - self.start_date).days > 1826:  # 5 years max span
                raise ValueError("Date range query span cannot exceed 5 years.")
        return self
```

#### D. Regression Verification
Added in `tests/security/test_transaction_validation.py`:
- `test_date_range_validation_rejects_inverted_dates`: Verified `start_date > end_date` returns HTTP 422 Unprocessable Content.
- `test_date_range_validation_rejects_excessive_span`: Verified date range spanning > 5 years is rejected with HTTP 422.
- `test_date_filtering_returns_transactions_within_window`: Verified valid temporal queries accurately filter transactions.

---

### 2.4 Weakness 4: Category BOLA Authorization & System Immutability Protection (SEC-006 / CWE-285)

#### A. Problem Description & Root Cause
In the initial baseline, category operations were limited to `GET` and `POST`. No endpoints existed for updating or deleting categories. Furthermore, if a user attempted to delete a category referenced by existing transactions, unhandled database foreign key constraints would trigger an internal server error (`HTTP 500`). Most critically, system default categories lacked explicit immutability guards against unauthorized mutation.

#### B. Security Impact
1. System categories could potentially be modified or deleted if administrative routes were exposed without strict role boundaries.
2. Users could accidentally or maliciously orphan active transactions, causing ledger inconsistencies.
3. Lack of tenant isolation on category updates could result in Broken Object Level Authorization (BOLA / IDOR).

#### C. Code Fix & Refactoring
1. Added `PUT /api/v1/categories/{category_id}` and `DELETE /api/v1/categories/{category_id}`.
2. Enforced strict system category immutability: attempts to modify or delete system categories (`is_system == True`) are rejected with `HTTP 403 Forbidden`.
3. Scoped all custom category mutations to the authenticated user (`WHERE id = :id AND user_id = :uid`). Cross-tenant modifications return `HTTP 404 Not Found` (anti-enumeration).
4. Added active transaction dependency checks before deletion: if a custom category has associated transactions, the request is rejected with `HTTP 400 Bad Request` and an explicit remediation message.

```python
# Fixed src/app/services/category_service.py
def delete_category(self, db: Session, category_id: int, user_id: int) -> None:
    category = self.category_repo.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    if category.is_system:
        raise HTTPException(status_code=403, detail="System default categories cannot be deleted.")
    if category.user_id != user_id:
        raise HTTPException(status_code=404, detail="Category not found.")

    # Guard active transactions
    active_count = db.query(Transaction).filter(
        Transaction.category_id == category_id,
        Transaction.user_id == user_id,
    ).count()
    if active_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category '{category.name}' because it contains {active_count} active transaction(s). Reassign them first."
        )

    self.category_repo.delete_custom(db, category_id, user_id)
```

#### D. Regression Verification
Created `tests/security/test_category_authz.py`:
- `test_cannot_modify_or_delete_system_categories`: Verifies HTTP 403 when attempting to edit/delete system categories.
- `test_cannot_modify_or_delete_other_user_category`: Verifies HTTP 404 anti-enumeration when attempting to access another user's category.
- `test_cannot_delete_category_with_active_transactions`: Verifies HTTP 400 when attempting to delete a category that has linked transactions.
- `test_can_update_and_delete_empty_custom_category`: Verifies successful lifecycle management for owned, unused custom categories.

---

## 3. Comprehensive Verification & Quality Gates

The complete automated security build pipeline (`scripts/build.ps1`) was executed to validate the refactored codebase against all quality gates:

```
[1/4] Secret Scanner & Git Hygiene Verification ................. PASSED (0 hardcoded secrets)
[2/4] Ruff Code Quality & Static Analysis ....................... PASSED (0 linting errors)
[3/4] Bandit Static Application Security Testing (SAST) ......... PASSED (0 vulnerabilities, 1608 LOC)
[4/4] Automated Pytest Test Suite ............................... PASSED (30 of 30 tests green)
```

### 3.1 Test Suite Breakdown (30 Automated Tests)
| Category | File | Count | Scope |
| :--- | :--- | :---: | :--- |
| **Workflow** | `test_workflow.py` | 1 | Complete registration, login, ledger creation, and CSV export lifecycle. |
| **Rate Limiting** | `test_auth_rate_limit.py` | 3 | Rate limiter DoS immunity, brute-force lockout, and reset logic. |
| **Category Authz** | `test_category_authz.py` | 4 | System immutability, BOLA tenant isolation, and dependency protection. |
| **IDOR / BOLA** | `test_idor_authorization.py` | 7 | Cross-tenant transaction read, update, delete, search, aggregation, and parameter injection. |
| **Reporting Security** | `test_reporting_security.py` | 3 | CSV/JSON tenant scoping and spreadsheet formula injection neutralization. |
| **Validation** | `test_transaction_validation.py` | 6 | Category type compatibility, date inversions, date span bounds, and temporal queries. |
| **Unit Security** | `test_security.py` | 6 | Argon2id hashing, password strength, JWT signing, token tampering, and formula escaping. |

---

## 4. Semantic Versioning & Traceability

- **Baseline Version:** `v1.0.0` (commit `914e034`)
- **Refactored Version:** `v1.1.0`
- **Specification Traceability:**
  - `SEC-001` / `SEC-002`: Password hashing & strength verification.
  - `SEC-003`: Authentication rate limiting with DoS immunity.
  - `SEC-004`: Revocable JWT session tokens.
  - `SEC-006`: Server-derived tenancy & anti-enumeration 404 responses.
  - `SEC-011`: Formula injection neutralization.
  - `SEC-017`: Input validation, boundary enforcement, and date limits.
  - `CWE-285` / `CWE-400` / `CWE-840` / `CWE-1236`: Vulnerability mitigations verified.
