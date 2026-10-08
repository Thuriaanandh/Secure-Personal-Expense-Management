# Phase 7, Part B: STRIDE Threat Analysis

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-SEC-STR01  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/security/stride.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. STRIDE Methodology Mapping to Approved DFD Elements

The STRIDE model classifies threats across six categories: **S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, and **E**levation of Privilege.

Threats are systematically identified across the DFD elements established in Phase 4:
- **Processes:** 1.0 Authentication, 2.0 Tenancy Gate, 3.0 Transaction Management, 4.0 Financial Analysis, 5.0 Secure Reporting, 6.0 Audit Logging.
- **Data Stores:** D1 User Store, D2 Category Store, D3 Transaction Ledger, D4 Audit Store.
- **Data Flows & Trust Boundaries:** TB1 (Client vs Server), TB2 (Server Execution), TB3 (Database Perimeter).

---

## 2. Systematic STRIDE Threat Inventory (11 Threats Detailed)

### Threat 1: Credential Guessing & Automated Password Spraying
- **Threat ID:** **THR-01**
- **DFD Element:** Process 1.0 (Authentication & Session Management) / External Boundary TB1.
- **Data Flow / Store:** Data Flow: `ClientUser -> Process 1.0` (Login Request).
- **STRIDE Category:** **Spoofing (S)**
- **Threat Description:** An adversary executes dictionary attacks or automated credential stuffing against `/api/v1/auth/login` to guess passwords and take over legitimate accounts.
- **Preconditions:** Target user account exists; attacker has network access to the login endpoint.
- **Impact:** Total account takeover; unauthorized access to victim's confidential financial records.
- **Likelihood:** **High** | **Impact:** **Critical** | **Overall Risk:** **Critical**
- **Mitigation:**
  1. Enforce strict rate limiting: at most 5 attempts per 15 minutes per IP/username (`SEC-003`).
  2. Slow down hashing evaluation using **Argon2id** (memory cost 64MB, time cost 3 iterations) (`SEC-001`).
  3. Enforce 10+ character password complexity checklist (`SEC-002`).
- **Detection Mechanism:** AuditLogger triggers security alert upon receiving 5 consecutive `AUTH_FAILURE` events within 15 minutes for a single IP or username (`SEC-015`).

---

### Threat 2: JWT Signature Forgery & Algorithm Confusion
- **Threat ID:** **THR-02**
- **DFD Element:** Process 2.0 (Authorization & Tenancy Gate) / Process 1.0.
- **Data Flow / Store:** Data Flow: `ClientUser -> Process 2.0` (Bearer Token Header).
- **STRIDE Category:** **Spoofing (S)**
- **Threat Description:** An attacker modifies token claims (e.g., forging `sub: 1`) and alters the token header to `alg: none` or exploits a weak HMAC secret key to forge a valid signature, bypassing authentication completely.
- **Preconditions:** Server accepts unsigned tokens or uses a predictable/short JWT secret key.
- **Impact:** Total authentication bypass; attacker can assume any arbitrary user identity.
- **Likelihood:** **Low** (with modern libraries) | **Impact:** **Critical** | **Overall Risk:** **High**
- **Mitigation:**
  1. Whitelist algorithms strictly to `HS256`; explicitly reject `alg: none` in JWT decoder (`SEC-004`).
  2. Mandate minimum 256-bit entropy secret key loaded exclusively from environment variables (`SEC-014`).
  3. Validate all standard claims: `exp` (<= 30 min), `iat`, and `nbf`.
- **Detection Mechanism:** Log and emit `AUTHZ_DENIED` with client IP whenever a token signature verification fails or an unapproved algorithm is detected.

---

### Threat 3: Broken Object-Level Authorization (BOLA / IDOR) on Transaction Mutation
- **Threat ID:** **THR-03**
- **DFD Element:** Process 3.0 (Transaction Management) / Process 2.0 / Store D3 (Transaction Ledger).
- **Data Flow / Store:** Data Flow: `Process 2.0 -> Process 3.0 -> Store D3`.
- **STRIDE Category:** **Tampering (T) & Elevation of Privilege (E)**
- **Threat Description:** An authenticated attacker alters the `transaction_id` parameter in `PUT /api/v1/transactions/{id}` or `DELETE /api/v1/transactions/{id}` to modify or delete financial records belonging to another user.
- **Preconditions:** Attacker has an active account; target transaction ID belongs to another tenant.
- **Impact:** Unauthorized alteration or deletion of another user's financial records; violation of data integrity and confidentiality.
- **Likelihood:** **High** (most prevalent API flaw) | **Impact:** **Critical** | **Overall Risk:** **Critical**
- **Mitigation:**
  1. The server extracts `user_id` strictly from the session token dependency (`Depends(get_current_active_user)`) (`SEC-005`).
  2. Database repository enforces compound query predicates: `WHERE id = :id AND user_id = :current_user.id`.
  3. If no row matches, return uniform `HTTP 404 Not Found` (anti-enumeration) (`SEC-006`).
- **Detection Mechanism:** Audit log captures `AUTHZ_DENIED` when a user queries or mutates an object not associated with their tenant ID.

---

### Threat 4: SQL Injection via Transaction Search & Filtering
- **Threat ID:** **THR-04**
- **DFD Element:** Process 3.0 (Transaction Management) / Data Store D3.
- **Data Flow / Store:** Data Flow: `ClientUser -> Process 3.0 -> Store D3`.
- **STRIDE Category:** **Tampering (T) & Information Disclosure (I)**
- **Threat Description:** An attacker injects malicious SQL fragments (e.g., `' OR '1'='1`) into the `keyword`, `category`, or `date` query parameters of the transaction search endpoint to bypass tenant isolation and dump all users' financial records.
- **Preconditions:** Dynamic SQL query construction using string concatenation or unescaped formatting.
- **Impact:** Total multi-tenant database compromise; massive cross-tenant financial data exfiltration.
- **Likelihood:** **Medium** | **Impact:** **Critical** | **Overall Risk:** **Critical**
- **Mitigation:**
  1. Use SQLAlchemy 2.0 ORM parameterized query builders exclusively; strictly prohibit raw string interpolation (`SEC-009`).
  2. Enforce Pydantic whitelist input validation on all search parameters (`SEC-008`).
  3. Static code analysis in CI via Bandit to detect unescaped SQL expressions.
- **Detection Mechanism:** Web Application Firewall / SQLAlchemy database query exceptions logged to audit stream with client IP and request trace.

---

### Threat 5: Spreadsheet / CSV Formula Injection in Financial Reports
- **Threat ID:** **THR-05**
- **DFD Element:** Process 5.0 (Secure Report Generation) / Trust Boundary TB1.
- **Data Flow / Store:** Data Flow: `Process 5.0 -> CSV Stream -> User Browser`.
- **STRIDE Category:** **Tampering (T)**
- **Threat Description:** An attacker inputs a malicious payload into a transaction description (e.g., `=cmd|' /C calc'!A0` or `=HYPERLINK(...)`). When an accountant or auditor downloads and opens the CSV report in Microsoft Excel, the spreadsheet executes the payload (CWE-1236).
- **Preconditions:** Attacker records a transaction containing formula trigger characters (`=`, `+`, `-`, `@`); victim downloads and opens the CSV export in desktop spreadsheet software.
- **Impact:** Client-side remote code execution on the workstation opening the report; exfiltration of sensitive spreadsheet contents.
- **Likelihood:** **Medium** | **Impact:** **High** | **Overall Risk:** **High**
- **Mitigation:**
  1. Implement `SecureCSVExporter` that inspects every exported cell. If any field starts with `=`, `+`, `-`, `@`, `\t`, or `\r`, prepend an apostrophe (`'`) (`SEC-011`).
  2. Enclose all CSV cells in RFC 4180 quotation marks (`csv.QUOTE_ALL`).
- **Detection Mechanism:** Input validation warnings and unit tests asserting formula trigger neutralization across exported datasets.

---

### Threat 6: Non-Repudiation Failure on Financial Mutations
- **Threat ID:** **THR-06**
- **DFD Element:** Process 6.0 (Security Audit Logging) / Store D4 (Audit Store).
- **Data Flow / Store:** Data Flow: `Process 3.0 -> Process 6.0 -> Store D4`.
- **STRIDE Category:** **Repudiation (R)**
- **Threat Description:** A user creates, modifies, or deletes significant financial records, or downloads a sensitive financial report, and later denies having performed the action because the system failed to maintain an immutable audit trail.
- **Preconditions:** Application performs ledger mutations without persisting audit records, or audit records lack timestamps and user IDs.
- **Impact:** Inability to perform forensic analysis; regulatory non-compliance; disputed financial states.
- **Likelihood:** **Medium** | **Impact:** **High** | **Overall Risk:** **Medium**
- **Mitigation:**
  1. Record immutable audit entries for all create, update, delete, and export events in `audit_logs` (`SEC-015`).
  2. Audit records must include: UTC timestamp, event type, caller `user_id`, client IP, resource, and HTTP status code.
- **Detection Mechanism:** Automated integration tests verifying that every database mutation produces a corresponding record in `audit_logs`.

---

### Threat 7: Transaction ID Enumeration & Information Disclosure
- **Threat ID:** **THR-07**
- **DFD Element:** Process 2.0 (Authorization Gate) / Process 3.0 (Anti-Enumeration Formatter).
- **Data Flow / Store:** Data Flow: `Process 3.0 -> Client Response`.
- **STRIDE Category:** **Information Disclosure (I)**
- **Threat Description:** An attacker sequentially probes integer transaction IDs (`/transactions/1`, `/transactions/2`). If the application returns `403 Forbidden` for other users' records and `404 Not Found` for non-existent records, the attacker infers which transaction IDs exist, discovering transaction volume and activity cadence.
- **Preconditions:** Differentiated error responses between unauthorized objects and non-existent objects.
- **Impact:** Metadata disclosure; enables targeted social engineering and timing analysis.
- **Likelihood:** **High** | **Impact:** **Medium** | **Overall Risk:** **Medium**
- **Mitigation:**
  1. Return uniform `HTTP 404 Not Found` for both non-existent records and cross-tenant records (`SEC-006`).
  2. Use public UUIDv4 identifiers or maintain uniform response times to prevent side-channel timing leaks.
- **Detection Mechanism:** Rate limiting on 404 responses; burst detection monitoring excessive 404 errors from a single IP.

---

### Threat 8: Credential & Token Leakage in Application Logs
- **Threat ID:** **THR-08**
- **DFD Element:** Process 6.0 (Security Audit Logging) / Store D4 / Stdout.
- **Data Flow / Store:** Data Flow: `Process 1.0 -> Process 6.0 -> Store D4`.
- **STRIDE Category:** **Information Disclosure (I)**
- **Threat Description:** Plaintext passwords, password hashes, JWT signatures, or Authorization headers are accidentally serialized into application log streams or database audit tables, exposing credentials to log consumers.
- **Preconditions:** Logging middleware logs entire raw HTTP request bodies or headers without redaction.
- **Impact:** Secondary credential compromise (CWE-532); persistent token exposure.
- **Likelihood:** **Medium** | **Impact:** **High** | **Overall Risk:** **High**
- **Mitigation:**
  1. Strict log masking: passwords, tokens, and authorization headers are sanitized before emitting log entries (`SEC-016`).
  2. Automated unit tests verifying that sensitive keys (`password`, `access_token`, `secret`) are scrubbed from log outputs.
- **Detection Mechanism:** Automated CI log scanning asserting zero credential tokens present in generated test log files.

---

### Threat 9: Denial of Service via Large Payload Flooding & Unbounded Queries
- **Threat ID:** **THR-09**
- **DFD Element:** Process 2.0 (Gateway) / Process 5.0 (Reporting Service).
- **Data Flow / Store:** Data Flow: `ClientUser -> Process 2.0 -> Process 5.0`.
- **STRIDE Category:** **Denial of Service (D)**
- **Threat Description:** An attacker submits excessively large request payloads (>50MB) or requests reports over unbounded multi-year date ranges without pagination, exhausting server memory and CPU resources.
- **Preconditions:** Lack of request body limits and unpaginated database queries.
- **Impact:** Container crash; service unavailability for all users (`NFR-002`).
- **Likelihood:** **Medium** | **Impact:** **High** | **Overall Risk:** **High**
- **Mitigation:**
  1. Global 1 MB request body limit enforced at the middleware layer (`SEC-017`).
  2. Mandatory query pagination: maximum 100 records per page.
  3. Memory-safe streaming response for CSV exports (`StreamingResponse`).
- **Detection Mechanism:** Container resource metrics monitoring CPU and memory limits in Kubernetes (`NFR-002`).

---

### Threat 10: Client-Supplied Tenant Parameter Spoofing (Parameter Pollution)
- **Threat ID:** **THR-10**
- **DFD Element:** Process 2.0 (Authorization & Tenancy Gate).
- **Data Flow / Store:** Data Flow: `ClientUser -> Process 2.0`.
- **STRIDE Category:** **Elevation of Privilege (E)**
- **Threat Description:** An attacker appends a client-supplied tenant parameter (e.g. `?user_id=2` or JSON body `{"user_id": 2}`) in a transaction creation or search request, attempting to execute actions on behalf of another user.
- **Preconditions:** Backend controller binds tenant identity to request parameters rather than server-derived token state.
- **Impact:** Cross-tenant ledger corruption; data creation under forged identities.
- **Likelihood:** **High** | **Impact:** **Critical** | **Overall Risk:** **Critical**
- **Mitigation:**
  1. Pydantic request DTOs configure `extra = "forbid"` and contain **NO `user_id` field** (`SEC-008`).
  2. Identity is extracted exclusively from the validated session token claims (`sub`) (`SEC-005`, `SEC-007`).
- **Detection Mechanism:** Negative security test asserting that submitting payloads with `user_id` causes schema rejection (`HTTP 422`).

---

### Threat 11: Stored Cross-Site Scripting (XSS) via Transaction Notes
- **Threat ID:** **THR-11**
- **DFD Element:** Process 3.0 (Transaction Management) / UI Component.
- **Data Flow / Store:** Data Flow: `ClientUser -> Store D3 -> UI View`.
- **STRIDE Category:** **Tampering (T) & Information Disclosure (I)**
- **Threat Description:** An attacker inputs malicious script tags (e.g., `<script>stealToken()</script>`) into a transaction description. If rendered unescaped in the dashboard or search view, the script executes in the victim's browser, stealing session tokens.
- **Preconditions:** Frontend renders raw HTML without context-aware escaping.
- **Impact:** Session hijacking; execution of arbitrary JavaScript in client browser context.
- **Likelihood:** **Medium** | **Impact:** **High** | **Overall Risk:** **High**
- **Mitigation:**
  1. All dynamic text rendered in Jinja2 templates undergoes context-aware HTML entity escaping (`SEC-010`).
  2. Deploy strict Content Security Policy (`CSP: default-src 'self'`).
  3. Store session tokens in `HttpOnly; SameSite=Strict; Secure` cookies.
- **Detection Mechanism:** Automated integration test injecting script tags and verifying escaped output (`&lt;script&gt;`).

---

## 3. STRIDE Threat Traceability Summary Table

| Threat ID | Threat Name | STRIDE Category | DFD Element | Risk Level | Primary Security Control |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **THR-01** | Password Brute Forcing | **S** | Process 1.0 | **Critical** | Rate Limiting & Argon2id (`SEC-001`, `SEC-003`) |
| **THR-02** | JWT Token Forgery | **S** | Process 2.0 | **High** | 256-bit HS256 Key & Claim Validation (`SEC-004`) |
| **THR-03** | BOLA / IDOR on Transactions | **T / E** | Process 3.0 / D3 | **Critical** | Server-Side Compound Query (`SEC-005`) |
| **THR-04** | SQL Injection in Search | **T / I** | Process 3.0 / D3 | **Critical** | Parameterized SQLAlchemy ORM (`SEC-009`) |
| **THR-05** | CSV Formula Injection | **T** | Process 5.0 | **High** | Prepend `'` on `=, +, -, @` (`SEC-011`) |
| **THR-06** | Financial Repudiation | **R** | Process 6.0 / D4 | **Medium** | Tamper-Resistant Audit Trail (`SEC-015`) |
| **THR-07** | ID Probing & Enumeration | **I** | Process 3.2 | **Medium** | Uniform `HTTP 404 Not Found` (`SEC-006`) |
| **THR-08** | Credential Leak in Logs | **I** | Process 6.0 / D4 | **High** | Strict Log Masking (`SEC-016`) |
| **THR-09** | DoS via Memory Exhaustion | **D** | Process 2.0 / 5.0 | **High** | 1MB Body Limit & Streaming (`SEC-017`) |
| **THR-10** | Tenant Parameter Tampering | **E** | Process 2.0 | **Critical** | Schema Stripping & Token Derivation (`SEC-007`)|
| **THR-11** | Stored XSS in Descriptions | **T / I** | Store D3 -> UI | **High** | Context HTML Escaping & CSP (`SEC-010`) |
