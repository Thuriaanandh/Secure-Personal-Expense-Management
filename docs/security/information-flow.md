# Phase 7, Part C: Information Flow Analysis

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-SEC-IF01  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/security/information-flow.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Flow Principles

Information Flow Analysis tracks how sensitive assets traverse trust boundaries, identifying transitions between untrusted and trusted domains, pinpointing potential leakage points, and verifying that authorization checkpoints are non-bypassable.

This document traces three critical assets:
1. **Asset 1: User Credentials (Plaintext Passwords & Password Hashes)**
2. **Asset 2: Authentication Session Tokens (JWT Access Tokens)**
3. **Asset 3: Financial Transaction Records & Exported Reports**

---

## 2. Asset 1 Information Flow: User Credentials

### 2.1 End-to-End Lifecycle Trace

```
+--------------------------------------------------------------------------------------------------+
| STEP 1: Client Input (Untrusted Browser - TB1)                                                   |
| - User enters plaintext password in HTML form (/login or /register)                             |
| - Masked input (type="password"), autocomplete="current-password"                                |
+--------------------------------------------------------------------------------------------------+
                                                |  HTTPS POST (TLS 1.3 Encryption)
                                                v  [CROSSES TRUST BOUNDARY TB1]
+--------------------------------------------------------------------------------------------------+
| STEP 2: Ingress & Validation (FastAPI Gateway - TB2)                                             |
| - TLS terminated; payload decoded into memory                                                    |
| - Pydantic DTO (UserCreateDTO) validates 10+ char policy; rejects invalid formats                |
| - Rate limiter checks IP/username threshold (max 5 attempts/15 min)                              |
+--------------------------------------------------------------------------------------------------+
                                                |  In-Memory Method Call
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 3: Cryptographic Processing (AuthService - TB2)                                             |
| - Passlib / Argon2id calculates salted cryptographic hash (64MB memory, 3 iterations)            |
| - Plaintext password is zeroized / dereferenced from memory                                      |
| - AuditLogger records AUTH_SUCCESS or AUTH_FAILURE (password explicitly stripped)                |
+--------------------------------------------------------------------------------------------------+
                                                |  Parameterized SQL INSERT/SELECT
                                                v  [CROSSES TRUST BOUNDARY TB3]
+--------------------------------------------------------------------------------------------------+
| STEP 4: Relational Persistence (Database Engine - TB3)                                           |
| - users table stores password_hash column only                                                   |
| - Plaintext password is NEVER written to disk, cache, or logs                                    |
+--------------------------------------------------------------------------------------------------+
```

### 2.2 Security Matrix for User Credentials Flow
- **Trusted / Untrusted Transitions:**
  - *Untrusted to Trusted:* User enters password in client browser; traverses untrusted public network into the trusted server boundary over TLS 1.3.
  - *Trusted to Internal:* Backend handles password in ephemeral memory; converts it to one-way hash before database persistence.
- **Trust Boundaries Crossed:** Crosses **TB1** (Client to Server) and **TB3** (Server to Database).
- **Security Controls Applied:**
  - TLS 1.3 in-transit encryption (`SEC-013`).
  - Strict input validation policy (`SEC-002`).
  - Rate limiting against brute forcing (`SEC-003`).
  - Argon2id cryptographic hashing with unique salt (`SEC-001`).
- **Possible Leakage Points & Countermeasures:**
  - *Leakage via URL query parameters:* Neutralized by using HTTP `POST` body exclusively.
  - *Leakage in server application logs (CWE-532):* Neutralized by strict audit masking (`SEC-016`).
  - *Leakage via database compromise:* Neutralized by Argon2id computational work factor.
- **Authorization Checkpoints:**
  - Pre-auth rate limit verification.
  - Constant-time password hash comparison preventing timing attacks.

---

## 3. Asset 2 Information Flow: Authentication Session Token (JWT)

### 3.1 End-to-End Lifecycle Trace

```
+--------------------------------------------------------------------------------------------------+
| STEP 1: Token Generation (AuthService - TB2)                                                     |
| - Upon successful login, AuthService generates JWT with claims: sub: user_id, exp: +30m, jti: uuid|
| - Cryptographically signed using HMAC-SHA256 with 256-bit server secret key                      |
+--------------------------------------------------------------------------------------------------+
                                                |  HTTPS Response Body / Set-Cookie (TLS 1.3)
                                                v  [CROSSES TRUST BOUNDARY TB1 (Server -> Client)]
+--------------------------------------------------------------------------------------------------+
| STEP 2: Client Token Storage (Untrusted Browser - TB1)                                           |
| - Token stored in browser memory or HttpOnly; SameSite=Strict; Secure cookie                     |
| - JavaScript cannot access HttpOnly cookie (XSS protection)                                      |
+--------------------------------------------------------------------------------------------------+
                                                |  HTTPS Request Header (Authorization: Bearer)
                                                v  [CROSSES TRUST BOUNDARY TB1 (Client -> Server)]
+--------------------------------------------------------------------------------------------------+
| STEP 3: Ingress Token Verification (Security Interceptor - TB2)                                  |
| - Depends(oauth2_scheme) intercepts incoming Bearer token                                        |
| - Validates HS256 signature against server SECRET_KEY                                            |
| - Validates exp, iat, and nbf claims; rejects expired tokens (HTTP 401)                           |
| - Checks jti against revoked_tokens table in Store D1 (revocation check)                         |
+--------------------------------------------------------------------------------------------------+
                                                |  Dependency Injection
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 4: Identity Context Injection (Domain Service - TB2)                                        |
| - sub claim extracted as authenticated current_user.id                                           |
| - Bound to request context; client-supplied tenant parameters are completely ignored             |
+--------------------------------------------------------------------------------------------------+
```

### 3.2 Security Matrix for Session Token Flow
- **Trusted / Untrusted Transitions:**
  - *Trusted to Untrusted:* Token issued by trusted server; stored within untrusted browser environment.
  - *Untrusted to Trusted:* Token presented in subsequent API requests; verified by server security interceptor.
- **Trust Boundaries Crossed:** Crosses **TB1** on issuance and on every protected HTTP invocation.
- **Security Controls Applied:**
  - HMAC-SHA256 signature verification (`SEC-004`).
  - Short lifetime (30 minutes) minimizing replay window.
  - `HttpOnly; SameSite=Strict` cookie flags neutralizing XSS exfiltration and CSRF.
  - Centralized revocation lookup (`revoked_tokens` table).
- **Possible Leakage Points & Countermeasures:**
  - *Leakage via Referer header:* Neutralized by passing token in HTTP `Authorization` header or cookie.
  - *Leakage via XSS:* Neutralized by CSP and HTML entity encoding.
  - *Token Tampering:* Neutralized by cryptographic signature validation rejecting modified payloads or `alg: none`.
- **Authorization Checkpoints:**
  - Global FastAPI dependency `get_current_active_user` acts as the mandatory gatekeeper for all protected routes.

---

## 4. Asset 3 Information Flow: Financial Transaction Records & Exported Reports

### 4.1 End-to-End Lifecycle Trace

```
+--------------------------------------------------------------------------------------------------+
| STEP 1: Transaction Request (Untrusted Browser - TB1)                                            |
| - User initiates transaction search, query, or CSV export request                               |
| - Transmits filter criteria + Authorization: Bearer <token> over HTTPS                           |
| - Attacker attempts parameter tampering: ?user_id=999                                            |
+--------------------------------------------------------------------------------------------------+
                                                |  HTTPS GET /api/v1/transactions
                                                v  [CROSSES TRUST BOUNDARY TB1]
+--------------------------------------------------------------------------------------------------+
| STEP 2: Authorization & Identity Extraction Gate (TB2)                                           |
| - Token validated; current_user.id (e.g. 101) derived from verified claims                       |
| - Any client-supplied user_id (999) is stripped/discarded                                        |
| - Pydantic validates search parameters (regex, date formats)                                     |
+--------------------------------------------------------------------------------------------------+
                                                |  Tenant-Scoped Service Invocation
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 3: Compound Query Construction (TransactionRepository - TB2)                                |
| - Repository constructs parameterized query hardcoding tenant boundary:                          |
|   WHERE user_id = :current_user_id AND ...                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |  Parameterized SQL Execution
                                                v  [CROSSES TRUST BOUNDARY TB3]
+--------------------------------------------------------------------------------------------------+
| STEP 4: Relational Retrieval (Database Engine - TB3)                                             |
| - Query planner executes compound index scan: idx_txn_user_date                                  |
| - Database returns solely rows belonging to user_id = 101                                        |
+--------------------------------------------------------------------------------------------------+
                                                |  Query Results Returned
                                                v  [CROSSES TRUST BOUNDARY TB3 (DB -> Server)]
+--------------------------------------------------------------------------------------------------+
| STEP 5: Report Sanitization & Streaming (ReportingService - TB2)                                 |
| - SecureCSVExporter checks every cell against formula triggers (=, +, -, @)                      |
| - Prepends single quote (') to neutralize spreadsheet formula execution (CWE-1236)               |
| - Formats RFC-4180 CSV stream directly in memory                                                 |
| - AuditLogger emits REPORT_EXPORTED event                                                        |
+--------------------------------------------------------------------------------------------------+
                                                |  Streaming HTTP Response (TLS 1.3)
                                                v  [CROSSES TRUST BOUNDARY TB1 (Server -> Client)]
+--------------------------------------------------------------------------------------------------+
| STEP 6: Client Display / Download (Browser - TB1)                                                |
| - Client receives sanitized CSV stream or JSON DTO                                               |
| - Opened safely in Excel/Calc without risk of remote formula execution                           |
+--------------------------------------------------------------------------------------------------+
```

### 4.2 Security Matrix for Financial Records Flow
- **Trusted / Untrusted Transitions:**
  - *Untrusted to Trusted:* Search filters enter backend; sanitized by Pydantic.
  - *Trusted to Internal:* Server derives caller identity; constructs scoped query for database.
  - *Internal to Untrusted:* Server serializes records; neutralizes formula injection; streams to browser.
- **Trust Boundaries Crossed:** Crosses **TB1** (Client/Server) twice, and **TB3** (Server/Database) twice.
- **Security Controls Applied:**
  - Server-side tenant derivation (`SEC-005`).
  - Compound query scoping (`WHERE id = :id AND user_id = :uid`).
  - Parameterized ORM execution (`SEC-009`).
  - Formula injection neutralization (`SEC-011`).
  - Memory streaming without temporary file disk caching.
- **Possible Leakage Points & Countermeasures:**
  - *BOLA / IDOR bypass:* Neutralized by removing `user_id` from client request schema and using compound query.
  - *Cross-tenant bulk export leakage:* Neutralized by binding export query to `current_user.id`.
  - *CSV formula execution (CWE-1236):* Neutralized by prepending `'` to trigger symbols.
- **Authorization Checkpoints:**
  - Token signature verification at the API Gateway.
  - Compound tenant filter verification in the Repository layer.
  - Anti-enumeration uniform 404 response on single-record lookups.
