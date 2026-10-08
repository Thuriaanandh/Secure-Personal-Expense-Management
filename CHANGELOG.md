# Changelog

All notable changes to the **Secure Personal Expense Management Application (SPEMA)** project are documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
