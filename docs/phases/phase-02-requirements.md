# Phase 2: Requirements Engineering

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-DOC-PH02  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/phases/phase-02-requirements.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Requirements Baseline

Building directly upon the approved Phase 1 Rugged Agile process model (`docs/phases/phase-01-agile.md`), Phase 2 specifies the formal Software Requirements Specification (SRS) for the **Secure Personal Expense Management Application (SPEMA)**.

### Primary Security Mandate
> **An authenticated user must not be able to access, modify, search, aggregate, or report on another user's financial records.**
> 
> This constraint is non-negotiable and absolute. It must be enforced server-side at the service and data-access layer. Authorization logic must derive user identity strictly from the cryptographically verified session token and reject or ignore any client-supplied user identifiers.

---

## 2. Stakeholders & User Taxonomy

### 2.1 Stakeholder Analysis
| Stakeholder | Description | Primary Interest | Security Concern |
| :--- | :--- | :--- | :--- |
| **Account Owner (End User)** | Individual utilizing the application to manage personal income, expenses, and budgets. | Intuitive interface, real-time summaries, accurate reporting, privacy. | Zero unauthorized visibility of their financial data by any other party. |
| **Security Auditor / Examiner** | Academic/laboratory examiner evaluating SSDLC artifacts and compliance against OWASP/NIST standards. | Verifiable security traceability, comprehensive documentation, test evidence. | Identification of IDOR, injection, session spoofing, and insecure secrets. |
| **DevOps / System Administrator** | Operations role responsible for container deployment, runtime health, and environment configuration. | High availability, minimal resource overhead, declarative Kubernetes manifests. | Container escape, credential leakage, privilege escalation, unpatched CVEs. |
| **Application Developer** | Engineering team implementing code according to Rugged Scrum and XP practices. | Clean architectural boundaries, testability, actionable specifications. | Introduction of authorization regressions, dependency vulnerabilities. |

### 2.2 User Types & Roles
1. **Anonymous / Unauthenticated Visitor:**
   - Permissions: Access public landing page, user registration (`POST /api/v1/auth/register`), and user login (`POST /api/v1/auth/login`).
   - Restrictions: Strictly blocked from all transaction, category, summary, search, report, and profile endpoints.
2. **Authenticated Account Owner (Standard User):**
   - Permissions: Full CRUD access over *their own* financial transactions, custom categories, monthly summaries, search queries, and exported reports.
   - Restrictions: Physically blocked from viewing, modifying, searching, aggregating, or generating reports on any data belonging to other accounts.
3. **System Administrator (DevOps / Site Reliability Role):**
   - Permissions: Inspect application liveness and readiness (`GET /healthz`), container resource metrics.
   - Restrictions: Under the Zero-Trust Data Isolation policy, the Administrator role has **no business-level access to read, decrypt, or alter individual users' financial transaction records**.

### 2.3 External Actors & Trusted Boundaries
- **User Agent (Browser / Mobile Web):** Untrusted boundary communicating strictly over TLS 1.3 / HTTPS.
- **Server Execution Environment:** Trusted boundary hosting the FastAPI application runtime.
- **Data Store (Relational Database - SQLite / PostgreSQL):** Trusted relational store enforcing foreign key constraints and transactional ACID boundaries.
- **System Hardware Clock (NTP):** Trusted server-side time reference for deterministic session expiry and audit log timestamps.
- *(Note: To maintain strict privacy and minimize external attack surfaces, no third-party tracking, advertising, or external analytics integrations are permitted).*

---

## 3. Data & Asset Classification (CIA Matrix)

Every critical data asset managed by SPEMA is categorized according to the **Confidentiality, Integrity, and Availability (CIA)** triad:

| Asset ID | Asset Name | Description | Confidentiality | Integrity | Availability | Justification |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **AST-01** | **User Credentials** | Passwords, password hashes (Argon2id), salt values. | **Critical** | **Critical** | **High** | Compromise enables complete account takeover and data exfiltration. |
| **AST-02** | **Session Tokens** | Signed JWT access tokens, refresh tokens. | **Critical** | **Critical** | **High** | Token forgery or theft allows impersonation and bypasses authentication. |
| **AST-03** | **Transaction Records** | Amounts, dates, transaction type (income/expense), category, descriptions. | **High** | **High** | **High** | Highly sensitive private financial records; loss of integrity distorts financial balance. |
| **AST-04** | **Financial Summaries & Reports** | Monthly aggregations, CSV/PDF exported financial statements. | **High** | **High** | **Medium** | Aggregated view of personal net worth and spending habits. |
| **AST-05** | **Audit & Security Logs** | Timestamped logs of auth attempts, authorization failures, and data mutations. | **Medium** | **Critical** | **High** | Critical for forensic investigation; must be tamper-resistant and immutable. |
| **AST-06** | **Application Secrets** | JWT signing secret keys, database credentials, environment variables. | **Critical** | **Critical** | **Critical** | Key leakage compromises all cryptographic trust across the entire platform. |
| **AST-07** | **PII (User Profile)** | User email address, username, account registration timestamp. | **High** | **High** | **High** | Protected under GDPR/privacy principles; subject to enumeration attacks. |

---

## 4. Functional Requirements (FR)

All requirements are prioritized using the **MoSCoW** convention (*Must have, Should have, Could have, Won't have*).

| ID | Functional Requirement Description | Priority | Traceability / Rationale |
| :---: | :--- | :---: | :--- |
| **FR-001** | **User Registration:** The system shall allow an unauthenticated user to register a unique account by providing an email, username, and password satisfying the password policy. | **Must** | Core functionality #1; enables user onboarding. |
| **FR-002** | **User Authentication:** The system shall verify user credentials against securely stored Argon2id hashes and issue a cryptographically signed, short-lived JWT token upon success. | **Must** | Core functionality #1 & #2; baseline identity establishment. |
| **FR-003** | **User Logout & Session Termination:** The system shall provide an endpoint to terminate active sessions and instruct client storage to discard credentials. | **Must** | Core functionality #2; prevents session hijacking on shared devices. |
| **FR-004** | **Record Income Transaction:** The system shall allow an authenticated user to record an income transaction with positive numerical amount, date, category, and optional description. | **Must** | Core functionality #3; core financial ledger entry. |
| **FR-005** | **Record Expense Transaction:** The system shall allow an authenticated user to record an expense transaction with positive numerical amount, date, category, and optional description. | **Must** | Core functionality #4; core financial tracking entry. |
| **FR-006** | **Transaction Categorization:** The system shall allow users to assign predefined (e.g., Salary, Food, Rent, Utilities, Entertainment) or custom categories to transactions. | **Must** | Core functionality #5; enables financial analysis. |
| **FR-007** | **Monthly Financial Summaries:** The system shall calculate and display aggregated monthly income, total expenses, net balance, and category-wise spending for the authenticated user. | **Must** | Core functionality #6; essential user financial dashboard. |
| **FR-008** | **Search and Filter Transactions:** The system shall allow users to search transactions by keyword, date range (start/end date), category, transaction type, and minimum/maximum amount. | **Must** | Core functionality #7; transaction discovery and audit. |
| **FR-009** | **Transaction Mutation & Deletion:** The system shall permit an authenticated user to update or delete an existing transaction, provided that transaction strictly belongs to that user. | **Must** | Core functionality #9; lifecycle management of ledger entries. |
| **FR-010** | **Financial Report Generation:** The system shall export filtered or full monthly transaction records into downloadable CSV reports formatted securely. | **Must** | Core functionality #8; portable financial record keeping. |
| **FR-011** | **Account Profile Management:** The system shall allow an authenticated user to view their account details and change their password by supplying their current password. | **Should** | Lifecycle maintenance; password rotation. |
| **FR-012** | **System Liveness & Readiness:** The system shall provide unauthenticated health check endpoints (`/healthz`, `/readyz`) reporting service status for container orchestrators. | **Must** | Core functionality #11; Kubernetes integration. |

---

## 5. Non-Functional Requirements (NFR)

| ID | Category | Requirement Description | Priority | Verification Method |
| :---: | :--- | :--- | :---: | :--- |
| **NFR-001** | **Performance** | API endpoints shall process and return responses within 200 ms under a nominal load of 50 concurrent requests. | **Should** | Load testing via Locust / Apache Bench. |
| **NFR-002** | **Scalability & Resource** | Application containers shall not exceed 256 MB RAM and 0.5 CPU cores under baseline operation. | **Must** | Docker/Kubernetes cgroup resource limits verification. |
| **NFR-003** | **Data Integrity** | All financial transactions must adhere to ACID properties; calculations must use exact fixed-point decimal arithmetic (no floating-point rounding errors). | **Must** | Unit testing with exact 2-decimal arithmetic edge cases. |
| **NFR-004** | **Usability & Feedback** | The user interface shall provide clear, actionable validation feedback for user errors without leaking internal stack traces or database errors. | **Must** | Manual UI walkthrough and negative input testing. |
| **NFR-005** | **Maintainability** | Codebase shall follow PEP 8 standards, maintain type hints across all functions, and maintain minimum 85% test coverage. | **Must** | Automated Ruff linter and Pytest coverage gates in CI. |
| **NFR-006** | **Portability** | The application shall package into an OCI-compliant container image executable across Docker, Minikube, and Kubernetes. | **Must** | Automated Docker container build and container execution test. |
| **NFR-007** | **Zero Hardcoded Secrets** | No passwords, cryptographic keys, or credentials shall exist in source code or default configuration files. | **Must** | Automated secret detection (TruffleHog / GitGuardian / Bandit). |

---

## 6. Comprehensive Security Requirements (SEC)

Every security requirement is specified with its unique ID, concrete statement, technical rationale, MoSCoW priority, and verifiable verification method.

### 6.1 Authentication Requirements (AUTH)

#### SEC-001: Modern Password Hashing & Salt Generation
- **Requirement:** User passwords must never be stored in plaintext. Passwords must be hashed using **Argon2id** (memory cost: 65,536 KiB, time cost: 3 iterations, parallelism: 4) or **bcrypt** (work factor: 12) with a cryptographically secure random per-user salt.
- **Rationale:** Protects credential database against offline dictionary and GPU/ASIC rainbow table attacks if the database is leaked.
- **Priority:** **Must**
- **Verification Method:** Unit test asserting password hash format, salt randomness, and verification latency (> 100ms per hash computation).

#### SEC-002: Password Policy Enforcement
- **Requirement:** Passwords must be at least 10 characters in length and contain at least one uppercase letter, one lowercase letter, one numeric digit, and one special symbol. Passwords matching common dictionary lists or the user's email/username must be rejected.
- **Rationale:** Prevents weak credential creation and reduces susceptibility to credential stuffing.
- **Priority:** **Must**
- **Verification Method:** Negative unit test suite attempting registration with weak, short, and dictionary passwords.

#### SEC-003: Rate Limiting & Brute Force Defense
- **Requirement:** The authentication endpoints (`/auth/login`, `/auth/register`) must enforce rate limiting permitting at most 5 attempts per IP address/username combination per 15-minute window. Excess attempts must return `HTTP 429 Too Many Requests`.
- **Rationale:** Prevents automated credential guessing and denial-of-service on password hashing routines.
- **Priority:** **Must**
- **Verification Method:** Automated test firing 10 rapid login attempts and confirming HTTP 429 on the 6th request.

#### SEC-004: Cryptographic Session Token Security
- **Requirement:** Authentication tokens must be digitally signed JSON Web Tokens (JWT) using HMAC-SHA256 (HS256) with a minimum 256-bit entropy secret key. Tokens must include an expiration time (`exp`) not exceeding 30 minutes, an issued-at claim (`iat`), and user subject identifier (`sub`).
- **Rationale:** Prevents token tampering, replay attacks, and perpetual session compromise.
- **Priority:** **Must**
- **Verification Method:** Automated test verifying signature validation, algorithm header tampering rejection (e.g. `alg: none`), and expired token rejection.

---

### 6.2 Authorization & Multi-Tenant Isolation Requirements (AUTHZ) — *Core Mandate*

#### SEC-005: Server-Side Multi-Tenant Isolation (Primary Security Mandate)
- **Requirement:** **An authenticated user must NEVER be able to access, modify, search, aggregate, or report on another user's financial records.**
  - Identity must be extracted strictly from the cryptographically verified session token.
  - The application must reject, ignore, or strip any client-supplied `user_id` or tenant parameter.
  - Every transaction lookup, mutation, deletion, monthly aggregation, and report generation must enforce tenant scoping at the database query boundary (`WHERE id = :transaction_id AND user_id = :authenticated_user_id`).
- **Rationale:** Complete elimination of Broken Object-Level Authorization (BOLA / IDOR / OWASP API1:2023) and cross-tenant financial data breaches.
- **Priority:** **Must**
- **Verification Method:** Automated negative integration test: User A creates Transaction `T1`. User B attempts to:
  1. `GET /api/v1/transactions/T1`
  2. `PUT /api/v1/transactions/T1`
  3. `DELETE /api/v1/transactions/T1`
  4. Search transactions containing `T1`
  5. Generate a report encompassing `T1`  
  All attempts by User B must fail with `HTTP 404 Not Found` and leave `T1` completely unmodified and unexposed.

#### SEC-006: Anti-Enumeration Error Handling
- **Requirement:** When an authenticated user requests a transaction identifier that belongs to another user, the API must return `HTTP 404 Not Found` identical to the response returned for a non-existent identifier. The system must **never return `HTTP 403 Forbidden`** in this scenario.
- **Rationale:** Returning `403 Forbidden` leaks existence of the record to an unauthorized attacker, enabling sequential ID enumeration and intelligence gathering.
- **Priority:** **Must**
- **Verification Method:** Automated security test comparing response code, response body structure, and latency between requests for non-existent IDs and cross-tenant IDs.

#### SEC-007: Defense Against Parameter Pollution & Client ID Spoofing
- **Requirement:** Any request containing conflicting, multiple, or client-supplied tenant identifiers (e.g. `?user_id=2` when token represents User 1) must either strictly disregard the parameter or reject the request with `HTTP 400 Bad Request`.
- **Rationale:** Prevents HTTP parameter pollution attacks designed to trick backend microservices or ORM filters.
- **Priority:** **Must**
- **Verification Method:** Negative API test sending payloads with forged `user_id` parameters and verifying query execution uses token subject only.

---

### 6.3 Input Validation & Injection Prevention (INP)

#### SEC-008: Strict Server-Side Whitelist Input Validation
- **Requirement:** All incoming request bodies, query strings, and path parameters must be validated using strongly-typed schemas (Pydantic v2). Transaction amounts must be strictly positive decimals (`0.01 <= amount <= 1,000,000.00`). Descriptions must be restricted to alphanumeric and standard punctuation with a maximum length of 255 characters.
- **Rationale:** Prevents invalid financial states, buffer abuses, and unexpected payload crashes.
- **Priority:** **Must**
- **Verification Method:** Fuzz testing and boundary value tests (negative amounts, zero amounts, strings exceeding 255 characters, script tags).

#### SEC-009: SQL Injection Prevention via Parameterized ORM Queries
- **Requirement:** All database interactions must use SQLAlchemy ORM expressions or explicitly parameterized SQL statements. Dynamic query construction using string formatting, interpolation, or concatenation is strictly prohibited across all repositories.
- **Rationale:** Complete elimination of SQL Injection (CWE-89 / OWASP A03:2021).
- **Priority:** **Must**
- **Verification Method:** Automated SAST scanning with Bandit and negative unit tests injecting SQL payloads (`' OR 1=1 --`, `UNION SELECT`) into all search and filter inputs.

#### SEC-010: Cross-Site Scripting (XSS) Prevention & Output Sanitization
- **Requirement:** All user-supplied text displayed in web templates or responses must undergo context-aware HTML entity encoding. The application must deploy a strict `Content-Security-Policy` (CSP) header prohibiting inline scripts and unauthorized external origins.
- **Rationale:** Neutralizes Stored and Reflected Cross-Site Scripting (XSS / CWE-79).
- **Priority:** **Must**
- **Verification Method:** Automated browser/HTTP tests submitting payload `<script>alert(1)</script>` into transaction descriptions and verifying it renders as `&lt;script&gt;alert(1)&lt;/script&gt;` with active CSP headers.

---

### 6.4 Secure Reporting & Output Integrity (REP)

#### SEC-011: Spreadsheet / CSV Formula Injection Prevention (CWE-1236)
- **Requirement:** During CSV financial report export, any data cell beginning with formula trigger symbols (`=`, `+`, `-`, `@`, `\t`, `\r`) must be neutralized by prepending an apostrophe (`'`) and enclosing the field in RFC 4180 quotes.
- **Rationale:** Prevents arbitrary command execution and remote data exfiltration when financial reports are opened by accountants or users in Microsoft Excel or LibreOffice Calc.
- **Priority:** **Must**
- **Verification Method:** Unit test submitting transactions with descriptions like `=cmd|' /C calc'!A0` and `=SUM(1+1)`, exporting the CSV, and asserting the output contains `'=cmd|...`.

#### SEC-012: Tenant-Scoped Report Aggregations
- **Requirement:** Report export queries must enforce the same compound tenant filter (`user_id == current_user.id`) as transaction queries. Reports must never allow passing arbitrary date spans or categories to aggregate cross-user metrics.
- **Rationale:** Prevents reporting modules from functioning as an architectural back door to leak aggregated financial data across tenants.
- **Priority:** **Must**
- **Verification Method:** Multi-tenant test verifying exported CSV line count matches the authenticated user's transaction count exactly.

---

### 6.5 Confidentiality & Cryptographic Security (CONF)

#### SEC-013: Transport Layer Security (TLS) Enforcement
- **Requirement:** All production communication must occur over TLS 1.3 (minimum TLS 1.2). The application must emit HTTP Strict Transport Security (`Strict-Transport-Security: max-age=31536000; includeSubDomains`) headers.
- **Rationale:** Protects data in transit from eavesdropping and man-in-the-middle (MitM) credential interception.
- **Priority:** **Must**
- **Verification Method:** Security header inspection in integration test suite.

#### SEC-014: Secret Management & Zeroization
- **Requirement:** Application secrets (database URLs, JWT secret keys, encryption keys) must be loaded exclusively from environment variables at runtime. Secrets must never be committed to git, logged, or bundled into Docker images.
- **Rationale:** Eliminates credential leakage in source control (CWE-798).
- **Priority:** **Must**
- **Verification Method:** Static repository audit, git history inspection, and container image layer inspection.

---

### 6.6 Audit & Security Logging Requirements (AUD)

#### SEC-015: Comprehensive Security Event Logging
- **Requirement:** The application must record structured JSON audit logs for the following security-critical events:
  1. Successful and failed authentication attempts.
  2. Authorization failures (e.g. cross-tenant access attempts).
  3. User registration and password modifications.
  4. Transaction creation, modification, and deletion.
  5. Financial report generation and data export events.
  Every log entry must record: `timestamp` (UTC ISO-8601), `event_type`, `user_id` (if authenticated), `client_ip`, `request_id`, `http_status`, and `outcome`.
- **Rationale:** Enables detection of ongoing attacks, forensic investigation, and compliance with security audit mandates.
- **Priority:** **Must**
- **Verification Method:** Integration test triggering each event type and validating log stream format and field presence.

#### SEC-016: Sensitive Data Log Masking
- **Requirement:** Audit logs must never contain sensitive data, including plaintext passwords, password hashes, JWT signatures, session tokens, or unmasked financial account credentials.
- **Rationale:** Prevents secondary credential theft via log harvesting (CWE-532).
- **Priority:** **Must**
- **Verification Method:** Log inspection test ensuring credentials passed in request payloads do not appear in logger outputs.

---

### 6.7 Availability & System Resilience (AVAIL)

#### SEC-017: Request Payload & Resource Limiting
- **Requirement:** The web server must reject request payloads exceeding 1 MB with `HTTP 413 Payload Too Large`. Database queries must implement mandatory pagination (`limit` capped at 100 records per page).
- **Rationale:** Prevents denial-of-service via memory exhaustion and uncontrolled database query spikes.
- **Priority:** **Must**
- **Verification Method:** Negative test sending >1 MB payload and asserting immediate 413 response.

#### SEC-018: Secure Error Handling & Stack Trace Suppression
- **Requirement:** In production mode, unhandled server exceptions must return a generic `HTTP 500 Internal Server Error` with a unique `error_reference_id`. Detailed debug traces and database schema specifics must never be returned to the client.
- **Rationale:** Prevents information disclosure (CWE-209) that facilitates targeted exploit construction.
- **Priority:** **Must**
- **Verification Method:** Fault injection test provoking an unhandled exception and inspecting the client response body.

---

## 7. Requirements Traceability & Verification Matrix

| Req ID | Category | MoSCoW | Risk Level | Primary Verification Method | Downstream Phase |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **FR-001** | Functional | Must | Medium | Automated Functional Test | Phase 3, 4, 12, 14 |
| **FR-002** | Functional | Must | High | Automated Auth Test | Phase 3, 5, 12, 14 |
| **FR-003** | Functional | Must | Medium | Session Logout Test | Phase 3, 12, 14 |
| **FR-004** | Functional | Must | Medium | Ledger Transaction Test | Phase 3, 4, 12, 14 |
| **FR-005** | Functional | Must | Medium | Ledger Transaction Test | Phase 3, 4, 12, 14 |
| **FR-006** | Functional | Must | Low | Category Validation Test | Phase 4, 12, 14 |
| **FR-007** | Functional | Must | High | Aggregation Calculation Test | Phase 3, 5, 12, 14 |
| **FR-008** | Functional | Must | Medium | Search Query Test | Phase 3, 5, 12, 14 |
| **FR-009** | Functional | Must | Critical | Ownership Mutation Test | Phase 3, 4, 7, 12 |
| **FR-010** | Functional | Must | High | Report Generation Test | Phase 3, 5, 12, 14 |
| **FR-011** | Functional | Should | Medium | Password Change Test | Phase 3, 12, 14 |
| **FR-012** | Functional | Must | Low | Health Check HTTP Test | Phase 13, 14 |
| **SEC-001** | Security | Must | Critical | Cryptographic Hash Benchmark | Phase 5, 7, 12, 14 |
| **SEC-002** | Security | Must | Medium | Policy Rejection Unit Test | Phase 5, 12, 14 |
| **SEC-003** | Security | Must | High | Rate Limiter Burst Test | Phase 5, 7, 12, 14 |
| **SEC-004** | Security | Must | Critical | JWT Tampering & Expiry Test | Phase 5, 7, 12, 14 |
| **SEC-005** | Security | Must | **Critical** | **Negative IDOR/BOLA Test Suite** | **Phase 3, 4, 7, 8, 12, 14** |
| **SEC-006** | Security | Must | High | Anti-Enumeration 404 Test | Phase 7, 12, 14 |
| **SEC-007** | Security | Must | High | Parameter Pollution Test | Phase 7, 12, 14 |
| **SEC-008** | Security | Must | High | Pydantic Schema Fuzz Test | Phase 5, 12, 14 |
| **SEC-009** | Security | Must | Critical | Bandit SAST / SQLi Test | Phase 7, 11, 14 |
| **SEC-010** | Security | Must | High | CSP Header & XSS Test | Phase 6, 7, 14 |
| **SEC-011** | Security | Must | High | Formula Sanitization Test | Phase 7, 12, 14 |
| **SEC-012** | Security | Must | Critical | Cross-Tenant Report Test | Phase 7, 12, 14 |
| **SEC-013** | Security | Must | High | TLS Config & Header Test | Phase 13, 15 |
| **SEC-014** | Security | Must | Critical | TruffleHog / Git Secret Scan | Phase 11, 14 |
| **SEC-015** | Security | Must | High | Audit Log Emission Test | Phase 5, 14, 15 |
| **SEC-016** | Security | Must | High | Log Credential Leak Test | Phase 14, 15 |
| **SEC-017** | Security | Must | Medium | Payload Limit Test | Phase 13, 14 |
| **SEC-018** | Security | Must | Medium | Fault Injection 500 Test | Phase 5, 14 |

---

## 8. High-Risk Requirements & Security Analysis

### 8.1 Highest-Risk Requirements Identified
1. **SEC-005 (Server-Side Multi-Tenant Isolation):**  
   *Risk:* A failure here directly causes catastrophic data breach (OWASP API1:2023 / BOLA), allowing any authenticated user to view, edit, or delete another user's private financial records.  
   *Mitigation:* Architectural invariant enforcing compound queries (`WHERE id = :id AND user_id = :current_user.id`) at the data access repository layer.
2. **SEC-004 (Cryptographic Session Token Security):**  
   *Risk:* Weak signing keys or missing algorithm verification allow attackers to forge arbitrary user identities, bypassing SEC-005 entirely.  
   *Mitigation:* Strong HMAC-SHA256 secret key generation via environment variables, strict token expiration, and rejection of `alg: none`.
3. **SEC-009 (SQL Injection Prevention):**  
   *Risk:* Dynamic query concatenation in search or filtering allows complete database dump and tenant boundary bypass.  
   *Mitigation:* Exclusively parameterized SQLAlchemy ORM statements.
4. **SEC-011 (CSV Formula Injection Prevention):**  
   *Risk:* Malicious payloads embedded in transaction descriptions execute code on client workstations during financial reporting.  
   *Mitigation:* Automated character escaping and single-quote prepending for all formula symbols.

### 8.2 Specificity Verification for IDOR/BOLA Prevention
The authorization requirement (**SEC-005**) is explicitly designed to eliminate BOLA/IDOR by establishing three testable criteria:
1. **Source of Truth for Identity:** Identity is extracted exclusively from the validated cryptographic token claims; any client-provided user identifier is rejected or discarded.
2. **Query Scoping Invariant:** Every database query targeting transactions, categories, summaries, and reports includes an obligatory compound tenant filter matching the session user ID.
3. **Uniform Error Disclosure:** If an object does not exist or belongs to another user, the API uniformly returns `HTTP 404 Not Found`, preventing identifier enumeration.
