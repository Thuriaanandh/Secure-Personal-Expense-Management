# Phase 11: Secure Development and Build Environment

**Project:** Secure Personal Expense Management Application (SPEMA)  
**Curriculum:** 24CYS401 Secure Software Engineering Laboratory  
**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Release Tag:** `v1.0.0`

---

## 1. Executive Summary & Objective

Phase 11 transitions the approved architectural designs (Phases 1–8) and agile sprint backlogs (Phases 9–10) into a hardened, production-grade implementation and automated build environment. In strict conformance with the laboratory examination guidelines and secure software development lifecycle (SSDLC) principles, the project establishes a zero-trust software repository baseline backed by automated static analysis, secret scanning, dependency pinning, and negative security testing.

### Primary Security Mandate Enforcement

> *"An authenticated user must not be able to access, modify, search, aggregate or report on another user's financial records."*

Phase 11 guarantees this invariant through programmatic architecture enforcement:
1. **Zero Client Trust:** Identity is never derived from client-supplied parameters; all endpoints resolve tenancy strictly through cryptographically verified JWT tokens (`Depends(get_current_active_user)`).
2. **Compound Query Scoping:** Repositories mandate `user_id` on all query methods (`WHERE id = :id AND user_id = :uid`).
3. **Anti-Enumeration Guard (CWE-200 / SEC-006):** Cross-tenant lookup attempts emit uniform `HTTP 404 Not Found` responses to prevent resource enumeration.
4. **Formula Injection Neutralization (CWE-1236 / SEC-011):** Spreadsheet formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with `'` in memory during CSV generation.
5. **Deterministic Session Revocation (SEC-004):** Logout explicitly blacklists JWT token identifiers (`jti`) in a dedicated `revoked_tokens` table.

---

## 2. Hardened Toolchain & Dependency Inventory

All production and development dependencies are strictly pinned to exact versions with SHA cryptographic integrity verification to prevent supply chain poisoning (CWE-1357):

### 2.1 Production Dependencies (`requirements.txt`)
| Component | Pinned Version | Security Rationale |
| :--- | :---: | :--- |
| `fastapi` | `0.115.6` | Modern asynchronous web framework with native OpenAPI schema generation and dependency injection. |
| `uvicorn[standard]` | `0.34.0` | Minimal, high-performance ASGI server configured with secure request limits. |
| `sqlalchemy` | `2.0.36` | Industry-standard ORM enforcing parameterized prepared statements to neutralize SQL injection (CWE-89). |
| `pydantic` | `2.10.4` | Strict type validation with `extra = "forbid"` preventing parameter pollution and mass assignment (CWE-915). |
| `pydantic-settings` | `2.7.0` | Secure environment variable parsing preventing hardcoded secrets in source code. |
| `passlib[argon2,bcrypt]` | `1.7.4` | Robust password context supporting NIST-recommended password hashing algorithms. |
| `argon2-cffi` | `23.1.0` | Memory-hard, timing-attack-resistant password hashing (Argon2id, RFC 9106 / SEC-001). |
| `python-jose[cryptography]`| `3.3.0` | Cryptographic signing and validation of HMAC-SHA256 JWT bearer tokens (SEC-004). |
| `python-multipart` | `0.0.20` | Secure multipart form data parser with denial-of-service protections. |
| `jinja2` | `3.1.5` | Context-aware template engine with auto-escaping enabled to prevent Cross-Site Scripting (XSS / CWE-79). |
| `httpx` | `0.28.1` | Modern HTTP client for internal test suite fixtures. |
| `pytest` | `8.3.4` | Automated test execution framework. |
| `pytest-asyncio` | `0.25.0` | Async testing harness for FastAPI lifecycle testing. |
| `email-validator` | `2.3.0` | Robust RFC 5322 email syntax validation preventing injection in registration inputs. |

### 2.2 Security & Build Quality Tooling (`requirements-dev.txt`)
| Tool | Pinned Version | Function |
| :--- | :---: | :--- |
| `bandit` | `1.9.4` | Static Application Security Testing (SAST) analyzing AST for security flaws (CWE patterns). |
| `ruff` | `0.16.10` | High-performance Python linter and formatter enforcing secure coding conventions. |
| `pip-audit` | `2.7.3` | Software Bill of Materials (SBOM) and vulnerability scanner auditing dependency CVEs. |
| `coverage` | `7.6.9` | Test coverage measurement engine enforcing branch and statement coverage thresholds. |

---

## 3. Repository Architecture & Layout

The project follows a clean layered modular monolith pattern separating presentation, business logic, persistence, and database concerns:

```
Secure-Personal-Expense-Management/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI pipeline (lint, SAST, tests)
├── docs/                          # SSDLC Phase Documentation (Phases 01 - 16)
│   ├── phases/
│   ├── requirements/
│   ├── diagrams/
│   ├── security/
│   ├── ui/
│   └── uml/
├── scripts/
│   ├── build.ps1                  # Reproducible PowerShell build & test pipeline
│   └── security_check.py          # Pre-build secret scanner & git hygiene validator
├── src/
│   └── app/
│       ├── core/                  # Security primitives, settings, database session
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── dependencies.py    # Centralized auth gatekeeper (Depends(get_current_active_user))
│       │   └── security.py        # Argon2id hasher, JWT creator, password policy
│       ├── models/                # SQLAlchemy ORM models with compound tenancy constraints
│       │   ├── audit.py
│       │   ├── category.py
│       │   ├── transaction.py
│       │   └── user.py
│       ├── repositories/          # Data access layer (mandatory user_id scoping)
│       │   ├── audit_repository.py
│       │   ├── category_repository.py
│       │   ├── transaction_repository.py
│       │   └── user_repository.py
│       ├── routers/               # API route definitions
│       │   ├── auth.py            # Rate-limited auth routes
│       │   ├── categories.py
│       │   ├── health.py
│       │   ├── reports.py         # In-memory CSV/JSON export
│       │   ├── transactions.py
│       │   └── web.py             # Server-rendered Jinja2 UI views
│       ├── schemas/               # Pydantic validation DTOs (extra="forbid")
│       │   ├── category.py
│       │   ├── transaction.py
│       │   └── user.py
│       ├── services/              # Business logic & threat mitigations
│       │   ├── audit_service.py   # Sensitive PII redaction
│       │   ├── auth_service.py
│       │   ├── category_service.py
│       │   ├── reporting_service.py # CWE-1236 CSV formula neutralization
│       │   └── transaction_service.py
│       ├── templates/             # Warm editorial Jinja2 templates (Screens 1 - 6)
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── reports.html
│       │   └── transactions.html
│       └── main.py                # App factory, OWASP headers middleware, exception handlers
├── tests/
│   ├── conftest.py                # In-memory test DB, isolated client fixtures
│   ├── integration/
│   │   └── test_workflow.py       # End-to-end user lifecycle & ledger workflow
│   ├── security/
│   │   ├── test_idor_authorization.py # BOLA/IDOR negative authorization tests
│   │   └── test_reporting_security.py  # Tenancy & formula sanitization verification
│   └── unit/
│       └── test_security.py       # Password hashing, policy, tokens, formula escaping
├── .gitignore                     # Strict git hygiene ignoring credentials, DB, temp files
├── bandit.yaml                    # SAST scanner configuration
├── CHANGELOG.md                   # v1.0.0 release log
├── pyproject.toml                 # Project metadata, Ruff & Pytest settings
├── README.md                      # Architecture guide & build instructions
├── requirements.txt               # Pinned production dependencies
└── requirements-dev.txt           # Pinned development & security tooling
```

---

## 4. Security Quality Gates & Verification Results

Execution of `.\scripts\build.ps1` runs four automated security gates before any code baseline can be committed or deployed:

### Gate 1: Secret Scanner & Git Hygiene (`scripts/security_check.py`)
- **Objective:** Detect hardcoded API tokens, private keys, passwords, and `.env` leaks prior to git operations.
- **Result:** **PASSED** — 0 hardcoded credentials detected across 100% of tracked repository files.

### Gate 2: Code Quality & Static Linting (`ruff check src/ tests/`)
- **Objective:** Enforce idiomatic Python style, dead-code removal, import formatting, and static correctness.
- **Result:** **PASSED** — All checks passed with zero warnings or errors.

### Gate 3: Static Application Security Testing (`bandit -c bandit.yaml -r src/`)
- **Objective:** Scan Abstract Syntax Trees for injection vulnerabilities, insecure cryptographic primitives, and weak entropy.
- **Result:** **PASSED** — 0 vulnerabilities identified (High: 0, Medium: 0, Low: 0) across 1,474 lines of code scanned.

### Gate 4: Automated Test Suite (`pytest -v tests/`)
- **Objective:** Verify functionality, cryptographic algorithms, negative authorization boundaries, and formula escaping.
- **Result:** **PASSED** — **17 tests passed, 0 failures, 0 errors** in 4.84s.

```
============================= test session starts =============================
tests/integration/test_workflow.py::test_complete_user_lifecycle_and_ledger_workflow PASSED [  5%]
tests/security/test_idor_authorization.py::test_cannot_read_other_user_transaction PASSED [ 11%]
tests/security/test_idor_authorization.py::test_cannot_update_other_user_transaction PASSED [ 17%]
tests/security/test_idor_authorization.py::test_cannot_delete_other_user_transaction PASSED [ 23%]
tests/security/test_idor_authorization.py::test_cannot_search_or_list_other_user_transactions PASSED [ 29%]
tests/security/test_idor_authorization.py::test_cannot_aggregate_other_user_financials PASSED [ 35%]
tests/security/test_idor_authorization.py::test_reject_client_supplied_user_id PASSED [ 41%]
tests/security/test_idor_authorization.py::test_unauthenticated_requests_rejected PASSED [ 47%]
tests/security/test_reporting_security.py::test_csv_export_scopes_to_user_only PASSED [ 52%]
tests/security/test_reporting_security.py::test_csv_export_neutralizes_formula_injection PASSED [ 58%]
tests/security/test_reporting_security.py::test_json_export_scopes_to_user_only PASSED [ 64%]
tests/unit/test_security.py::test_password_hashing PASSED                [ 70%]
tests/unit/test_security.py::test_password_strength_validation PASSED    [ 76%]
tests/unit/test_security.py::test_jwt_token_creation_and_decoding PASSED [ 82%]
tests/unit/test_security.py::test_jwt_token_expiration PASSED            [ 88%]
tests/unit/test_security.py::test_jwt_token_tampered PASSED              [ 94%]
tests/unit/test_security.py::test_csv_formula_injection_sanitization PASSED [100%]
======================= 17 passed, 73 warnings in 4.84s =======================
```

---

## 5. Traceability to Previous SSDLC Phases

| Phase & Artifact | Implementation Realization in Phase 11 Baseline | Verification Method |
| :--- | :--- | :--- |
| **Phase 2 (Requirements)** | `FR-001` - `FR-012`, `SEC-001` - `SEC-018` realized across routers, services, and models. | 17 Automated tests in `tests/` |
| **Phase 3 (Use Cases & UML)** | Use Case controllers implemented in `src/app/routers/` (`auth.py`, `transactions.py`, `reports.py`). | `test_workflow.py` |
| **Phase 4 (ER & DFD)** | Relational schemas (`src/app/models/`) mirror ER diagram with foreign keys and compound tenancy indexes. | SQLAlchemy ORM DDL & SQLite tests |
| **Phase 5 (Architecture)** | Modular Monolith Layered Architecture with clean separation of Routers $\to$ Services $\to$ Repositories. | Codebase inspection & Ruff imports |
| **Phase 6 (UI Design)** | 6 Jinja2 templates faithfully reproduce the warm editorial wireframes without leaking account IDs. | `src/app/templates/` & `routers/web.py` |
| **Phase 7 (Threat Model)** | Mitigations for 11 STRIDE threats implemented (Argon2id, rate limiting, prepared statements, XSS auto-escaping). | Bandit SAST & `test_idor_authorization.py` |
| **Phase 8 (Attack Tree)** | Root goal attack paths neutralized (anti-enumeration 404s, query compound filters, formula neutralization). | `test_reporting_security.py` |

---

## 6. Release Baseline & Next Phase Hand-Off

With all 4 security quality gates verified green, the initial coherent release baseline is tagged as **`v1.0.0`** and committed to the Git version control system.

- **Git Commit Baseline:** Documented in Git log.
- **Git Release Tag:** `v1.0.0`
- **Next Phase:** Phase 12 (Secure Coding and Refactoring).
