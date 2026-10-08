# Changelog

All notable changes to the **Secure Personal Expense Management Application (SPEMA)** project are documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.3.0] - 2026-10-08

### Added
- **Central CI/CD Automated Quality & Security Gate (`.github/workflows/ci.yml`):**
  - Enhanced GitHub Actions workflow covering 13 comprehensive quality and security stages across 3 orchestrated jobs:
    1. Checkout repository
    2. Dependency installation (`pip install -r requirements.txt -r requirements-dev.txt`)
    3. Dependency vulnerability auditing (`pip-audit`)
    4. Secret hygiene & gitignore validation (`scripts/security_check.py`)
    5. Linting & code standards analysis (`ruff check src/ tests/`)
    6. Static Application Security Testing (`bandit -c bandit.yaml -r src/`)
    7. Unit tests (`pytest tests/unit/`)
    8. Integration tests (`pytest tests/integration/`)
    9. System & API tests (`pytest tests/api/`)
    10. Security & IDOR authorization isolation tests (`pytest tests/security/`)
    11. Property-based and fuzz testing (`pytest tests/property/`)
    12. Container build & non-root user verification (`docker build` + UID 10001 check)
    13. Kubernetes deployment validation (`kubectl kustomize k8s/ --dry-run=client`)
- **System and API Testing Suite (`tests/api/test_system_api.py`):**
  - Live probe verification for `/healthz` and `/readyz` endpoints.
  - OpenAPI 3.1.0 schema specification validation.
  - OWASP security headers enforcement verification (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`).
  - Web UI route accessibility and HTML content verification.
- **Hypothesis Property-Based & Fuzz Testing (`tests/property/test_property_based.py`):**
  - Formula injection invariant fuzzing (CWE-1236) across arbitrary Unicode text.
  - Password strength validator resilience and soundness invariants (CWE-20 / CWE-521).
  - Temporal query filter boundary invariants (inverted dates, spans > 5 years, leap years).
  - Financial ledger amount precision and boundary invariants ($0.01 to $1,000,000.00).
- **Comprehensive Authentication & Token Security Tests (`tests/security/test_auth_failures_and_tokens.py`):**
  - Invalid credentials and non-existent user rejections (HTTP 401).
  - Protected API routes authentication barrier enforcement.
  - Malformed JWT header and payload structural rejection.
  - HMAC-SHA256 signature tampering detection.
  - Expired token lifecycle rejection.
  - Revoked token enforcement via RFC 6750 case-insensitive Bearer logout.
  - Malicious SQL injection and XSS input validation rejection (HTTP 422).

### Fixed
- **Silent Token Revocation Bypass on Case-Insensitive Bearer Header (CWE-613 / CWE-384):**
  - Refactored `src/app/routers/auth.py` `logout` endpoint to handle RFC 6750 case-insensitive `bearer` authorization headers and arbitrary whitespace. Previously, non-standard headers bypassed the `startswith("Bearer ")` check, causing JWT decoding failures during revocation resulting in HTTP 200 without recording the token in `revoked_tokens`.
  - Added regression test `tests/security/test_auth_failures_and_tokens.py::test_revoked_token_regression_case_insensitive_logout`.
- **Unhandled ValidationError in Reports Filter Boundary (CWE-754 / CWE-20):**
  - Refactored `src/app/routers/reports.py` `export_csv_report` and `export_json_report` endpoints with robust exception handling around `TransactionFilterParams` instantiation. Inverted date ranges or spans > 5 years now return clean `HTTP 400 Bad Request` instead of uncaught `HTTP 500 Internal Server Error`.
  - Added regression test `tests/security/test_reporting_security.py::test_report_export_date_validation_regression`.
- **Web UI TemplateResponse Starlette Compatibility:**
  - Modernized all `templates.TemplateResponse` invocations in `src/app/routers/web.py` to use keyword arguments `request=request, name=..., context={...}`.

## [1.2.0] - 2026-10-08

### Added
- **Production-Hardened Containerization:**
  - Multi-stage Dockerfile based on `python:3.12-slim-bookworm` stripping build utilities from final runtime image.
  - Dedicated unprivileged non-root user and group `appuser:appgroup` (UID: 10001, GID: 10001, `/sbin/nologin`).
  - Native Docker container `HEALTHCHECK` periodically probing `/healthz`.
  - Comprehensive `.dockerignore` preventing leaks of Git history, SQLite databases, credentials, tests, and caches.
  - Zero baked secrets: all configurations injected dynamically via environment variables and Kubernetes Secrets.
- **Kubernetes Orchestration & Security Hardening (`k8s/`):**
  - Dedicated `spema` namespace enforcing Pod Security Standard `restricted` level.
  - Decoupled `ConfigMap` (`spema-config`) and `Secret` (`spema-secret`) configuration architecture.
  - `PersistentVolumeClaim` (`spema-data-pvc`, 500Mi) mounted at `/data` for durable database persistence.
  - Hardened single-replica `Deployment` enforcing `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, dropped capabilities (`ALL`), and `RuntimeDefault` seccomp profile.
  - HTTP liveness (`/healthz`) and readiness (`/readyz`) probes.
  - NodePort `Service` (`spema-service`) exposing port 8000 on node port 30080.
  - `NetworkPolicy` (`spema-network-policy`) restricting ingress to port 8000 and limiting egress.
  - Declarative bundling via `kustomization.yaml`.
- **Verification & Deployment Documentation:**
  - End-to-end integration verification test script (`scripts/test_k8s_deployment.py`).
  - Comprehensive deployment guide (`docs/deployment/docker-kubernetes.md`).
  - Phase 13 SSDLC phase document (`docs/phases/phase-13-containerization.md`).

## [1.1.0] - 2026-10-08

### Added
- **Custom Category Lifecycle Management:**
  - Added `PUT /api/v1/categories/{category_id}` and `DELETE /api/v1/categories/{category_id}` endpoints allowing users to update and delete their custom categories.
  - Category deletion enforces integrity constraints checking for active transaction dependencies, rejecting deletion with `HTTP 400 Bad Request` if transactions reference the category.
- **Transaction Temporal Filtering:**
  - Exposed `start_date` and `end_date` parameters on `GET /api/v1/transactions` with automated database query scoping.
- **Automated Security Regression Suite:**
  - `tests/security/test_auth_rate_limit.py`: Tests verifying rate limiter behavior (legitimate user immunity, lockout threshold enforcement, and success reset).
  - `tests/security/test_transaction_validation.py`: Tests verifying ledger compatibility rules, inverted date rejection, and maximum date span constraints.
  - `tests/security/test_category_authz.py`: Tests verifying system category immutability, tenant-isolated custom category authorization, and deletion integrity.

### Changed
- **Authentication Rate Limiter Refactoring (CWE-400 / SEC-003):**
  - Refactored sliding-window rate limiting in `src/app/routers/auth.py` so only failed authentication attempts increment the failure counter.
  - Added explicit rate-limit counter reset upon successful credential verification (`reset_rate_limit`), eliminating false-positive Denial-of-Service lockouts for valid users.
- **Ledger Typology Enforcement (CWE-840 / CWE-285):**
  - Refactored `TransactionService.create_transaction` and `TransactionService.update_transaction` to validate transaction type against category type (`INCOME`, `EXPENSE`, or `BOTH`). Mismatched classifications are rejected with `HTTP 400 Bad Request`.
- **Query Parameter Boundary Validation (CWE-20 / SEC-017):**
  - Enhanced `TransactionFilter` schema with Pydantic `@model_validator` rejecting inverted date windows (`start_date > end_date`) and spans exceeding 5 years (1826 days) to prevent resource exhaustion attacks.
- **Category Authorization & System Protection (SEC-006 / CWE-285):**
  - Enforced server-side tenancy scoping on category mutations (`WHERE id = :id AND user_id = :uid`).
  - System default categories (`is_system = True`) are rendered immutable across all mutation endpoints with `HTTP 403 Forbidden`.
  - Non-existent or foreign user categories return uniform `HTTP 404 Not Found` to prevent account/ID enumeration.

## [1.0.0] - 2026-10-08

### Added
- **Core Security Architecture:**
  - Mandatory server-side tenancy scoping on all database queries (`WHERE id = :id AND user_id = :uid`).
  - Zero-trust token resolution via FastAPI dependency injection (`Depends(get_current_active_user)`).
  - Pydantic models with strict payload sealing (`model_config = {"extra": "forbid"}`) to prevent client-supplied `user_id` injection.
  - Uniform `HTTP 404 Not Found` responses on unauthorized resource access to prevent ID enumeration (CWE-200 / SEC-006).
  - Sliding-window in-memory rate limiting on authentication endpoints to thwart brute-force and credential stuffing attacks (SEC-003).
  - Complete token revocation mechanism (`RevokedToken` model) allowing deterministic session invalidation upon logout (SEC-004).
  - Formula injection neutralization (CWE-1236 / SEC-011) prepending `'` to CSV export cells beginning with `=`, `+`, `-`, `@`, `\t`, or `\r`.
  - Comprehensive, tamper-evident audit logging (`AuditLog` model and `AuditService`) with automatic credential and PII masking.
  - Standardized OWASP secure HTTP response headers middleware (`CSP`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`).
- **Data Model & Persistence:**
  - Relational database schema with compound tenancy indexes: `users`, `categories`, `transactions`, `revoked_tokens`, `audit_logs`.
  - Automated seeding of 9 standard financial categories (`Salary`, `Groceries`, `Housing`, etc.) alongside user-scoped custom categories.
- **RESTful API Endpoints (`/api/v1`):**
  - Health checks: `/healthz`, `/readyz`.
  - Authentication: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/me`.
  - Transactions: `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`.
  - Categories: `GET /`, `POST /`.
  - Reports: `GET /api/v1/reports/summary`, `GET /api/v1/reports/export-csv`, `GET /api/v1/reports/export-json`.
- **Minimalist Editorial User Interface:**
  - Jinja2 server-rendered templates (`login.html`, `register.html`, `dashboard.html`, `transactions.html`, `reports.html`).
  - Strict anti-data leakage guidelines: zero account IDs in browser routes, client storage restricted to ephemeral access token.
- **Automated Verification & Build Environment:**
  - 17 automated tests covering unit security, BOLA/IDOR negative authorization, reporting sanitization, and end-to-end integration workflows.
  - Bandit SAST scan pipeline configured (`bandit.yaml`) with 0 issues identified.
  - Ruff linting and formatting configuration (`pyproject.toml`).
  - Secret scanning pre-build script (`scripts/security_check.py`) verifying clean git hygiene.
  - GitHub Actions CI workflow (`.github/workflows/ci.yml`).
