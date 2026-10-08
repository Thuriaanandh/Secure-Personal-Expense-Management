# Phase 7, Part A: Asset Inventory & Threat Modeling Framework

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-SEC-TM01  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/security/threat-model.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Threat Modeling Methodology & Scope

This threat model adopts the **STRIDE methodology** developed by Microsoft, applied directly to the approved Phase 4 Data Flow Diagrams (Context, Level 1, and Level 2) and Phase 5 Software Architecture.

### Core Security Scope & Objective
The fundamental goal of the threat model is to systematically identify, classify, and mitigate any technical vector that could violate the **Primary Security Mandate**:
> **An authenticated user must not be able to access, modify, search, aggregate, or report on another user's financial records.**

---

## 2. PART A — Security-Relevant Asset Inventory

Every critical system asset is cataloged with its unique identifier, owner, CIA classification, security importance, and primary engineering protection mechanism:

| Asset ID | Asset Name | Asset Owner | CIA Classification | Security Importance | Protection Mechanism |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **AST-01** | **User Credentials** *(Passwords & Salts)* | Account Owner / Auth System | **C: Critical**<br>**I: Critical**<br>**A: High** | Compromise enables complete account takeover and data exfiltration across all user records. | Modern **Argon2id** password hashing (`SEC-001`), per-user cryptographic salt, strict password policy (`SEC-002`), memory zeroization, no logging. |
| **AST-02** | **Session Tokens** *(JWT Access Tokens)* | Auth Subsystem / Active Session | **C: Critical**<br>**I: Critical**<br>**A: High** | Bearer proof of identity for all protected REST operations. Forgery or theft bypasses authentication. | **HMAC-SHA256** digital signature with 256-bit secret, 30-min expiration, JTI tracking in `revoked_tokens` table upon logout (`SEC-004`). |
| **AST-03** | **Transaction Records** *(Income & Expense Ledger)* | Authenticated Account Owner | **C: High**<br>**I: High**<br>**A: High** | Highly sensitive private financial records. Tampering distorts balance; leakage breaches privacy. | Server-side compound database query (`WHERE id = :id AND user_id = :current_user.id`), `NOT NULL` foreign key constraint (`SEC-005`). |
| **AST-04** | **Financial Summaries & Metrics** | Authenticated Account Owner | **C: High**<br>**I: High**<br>**A: Medium** | Aggregated view of personal net worth, savings rates, and category expenditures. | Server-side calculation scoped strictly to `WHERE user_id = :current_user.id`; fixed-point decimal arithmetic (`NFR-003`). |
| **AST-05** | **Exported Financial Reports** *(CSV / JSON)* | Authenticated Account Owner | **C: High**<br>**I: High**<br>**A: Medium** | Bulk exported statements. Opening in spreadsheet software introduces client-side code execution risks. | Dynamic memory streaming (no temp files), **Formula Injection Sanitization** (`=`/`+`/`-`/`@` prepended with `'`) (`SEC-011`, `SEC-012`). |
| **AST-06** | **Category Information** *(Taxonomies)* | System (Defaults) / User (Custom) | **C: Medium**<br>**I: High**<br>**A: High** | Financial categorization tags. Corruption breaks reporting and financial summaries. | Access filter (`WHERE is_system = TRUE OR user_id = :uid`), unique constraint `(user_id, name)` per tenant. |
| **AST-07** | **Security & Audit Logs** | Security Auditor / DevOps | **C: Medium**<br>**I: Critical**<br>**A: High** | Essential for forensic investigation, non-repudiation, and breach discovery. | Tamper-resistant append-only storage, credential masking (`SEC-016`), access restricted to administrative roles. |
| **AST-08** | **Application Secrets** *(JWT Secret, DB Passwords)* | DevOps / Runtime Environment | **C: Critical**<br>**I: Critical**<br>**A: Critical** | Root cryptographic trust. Compromise allows offline token generation and total database breach. | Injected strictly from OS environment variables (`SEC-014`), zero hardcoded secrets in source control or container images. |
| **AST-09** | **Relational Database Store** | Database Engine / DevOps | **C: Critical**<br>**I: Critical**<br>**A: Critical** | Persistent data store for all user partitions and audit records. | Parameterized ORM queries exclusively (`SEC-009`), container network isolation, least-privilege database user. |
| **AST-10** | **Application Source Code & Manifests** | Development Team | **C: Medium**<br>**I: High**<br>**A: High** | Source code integrity, container build configurations, and Kubernetes manifests. | Git branch protection, signed commits, automated SAST (Bandit) and dependency scanning in CI/CD (`NFR-005`). |

---

## 3. Threat Modeling Synthesis & Traceability

The threat modeling analysis proceeds across three complementary documents:
1. **STRIDE Analysis (`docs/security/stride.md`):** Systematic analysis of threats against all DFD elements and trust boundaries.
2. **Information Flow Analysis (`docs/security/information-flow.md`):** Deep tracing of sensitive assets across trust boundaries TB1, TB2, and TB3.
3. **Vulnerability Analysis (`docs/security/vulnerabilities.md`):** Identification and remediation of concrete vulnerabilities with CWE mapping and exploit scenarios.
