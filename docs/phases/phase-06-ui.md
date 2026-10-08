# Phase 6: User Interface Design

**Project Title:** Secure Personal Expense Management Application (SPEMA)  
**Document ID:** SPEMA-DOC-PH06  
**Course Code:** 24CYS401 – Secure Software Engineering Laboratory  
**Document Path:** `docs/phases/phase-06-ui.md`  
**Classification:** Laboratory Examination Artifact – High Integrity  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Visual Design Philosophy

Phase 6 establishes the user interface design for the Secure Personal Expense Management Application, derived from the functional requirements (`FR-001` - `FR-012`), security specifications (`SEC-001` - `SEC-018`), UML use cases (`UC-01` - `UC-16`), and presentation layer components defined in Phase 5.

### 1.1 Aesthetic Style: Artisanal Editorial Minimalism

The design explicitly avoids dark-mode neon aesthetics, garish gradients, or distracting visual noise. Instead, it adopts **Artisanal Editorial Minimalism**:
- **Canvas & Surface:** Warm canvas background (`#FBFBFA`), pure white card surfaces (`#FFFFFF`), with subtle sand-grey micro-borders (`#EAE8E3`).
- **Typography:** Refined editorial serif headers (*Newsreader* / serif aesthetic), paired with crisp humanist sans-serif body text (*Inter*) and tabular monospace numbers (`SF Mono` / monospace) for currency values to guarantee vertical decimal alignment without layout distortion.
- **Color Palette:**
  - **Primary Action & Positive Income:** Deep Forest Pine (`#2C4C3B` / `#F4F7F5` tint).
  - **Expense & Destructive Warnings:** Muted Terracotta / Sienna (`#A64B2A` / `#FDF3E7` tint).
  - **Text Hierarchy:** Deep charcoal (`#242423`) for primary headers, stone slate (`#636361`) for labels, and warm pebble (`#8C8B88`) for metadata.
  - **Dividers & Focus Rings:** Sand grey (`#EAE8E3`) borders and accessible sage focus indicators (`#8DAA9D`).

```
+--------------------------------------------------------------------------------------------------+
| Visual Theme Matrix: Artisanal Editorial Minimalism                                              |
| Canvas: #FBFBFA | Cards: #FFFFFF | Borders: #EAE8E3 | Text: #242423 | Accent Pine: #2C4C3B       |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Comprehensive Screen Specifications

### 2.1 Screen 1: Login (`/login`)
- **Visual Wireframe:** [`docs/ui/screen1_login.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen1_login.svg)

```
+--------------------------------------------------------------------------+
|                               S P E M A                                  |
|                             Welcome Back                                 |
|               Access your private personal expense ledger                |
|                                                                          |
|   Email Address:                                                         |
|   [ user@example.com                                                 ]   |
|                                                                          |
|   Password:                                                              |
|   [ ***********                                                      ]   |
|                                                                          |
|   [ (o) Protected by Argon2id & Rate-Limited Login                   ]   |
|                                                                          |
|   [                       Sign In to Account                         ]   |
|                                                                          |
|                   Don't have an account? Register securely               |
|                 End-to-End Tenant Isolation Enforced Server-Side         |
+--------------------------------------------------------------------------+
```

- **User:** Unauthenticated Visitor / Returning Account Owner.
- **Goal:** Authenticate securely into the personal expense management session.
- **Navigation:** Standalone clean card; link to Registration (`/register`).
- **Inputs:**
  - `email`: Text input, type `email`, required.
  - `password`: Password input, type `password`, required.
- **Validation:**
  - Client-side: Non-empty email format checking.
  - Server-side: Rate-limited verification against Argon2id hash (`SEC-001`, `SEC-003`).
- **Success Feedback:** Smooth redirect to `/dashboard`; JWT issued and securely stored.
- **Error Feedback:** Uniform error message: *"Invalid email or password"*. Never reveals whether the email exists (neutralizes username enumeration). If rate limit triggers, displays: *"Too many failed attempts. Please retry in 15 minutes."*
- **Authorization Considerations:** No authenticated state required. Successful login binds session exclusively to the returned user claims.
- **Confidentiality Considerations:** Password masked; `autocomplete="current-password"`; credentials transmitted strictly over TLS 1.3 POST body (never in URLs).
- **Secure Display Considerations:** Zero server debug traces rendered on authentication failures.

---

### 2.2 Screen 2: Registration (`/register`)
- **Visual Wireframe:** [`docs/ui/screen2_register.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen2_register.svg)

```
+--------------------------------------------------------------------------+
|                               S P E M A                                  |
|                         Create Private Ledger                            |
|          Your financial data is completely isolated from other users     |
|                                                                          |
|   Email Address:                                                         |
|   [ you@domain.com                                                   ]   |
|                                                                          |
|   Username:                                                              |
|   [ finance_user                                                     ]   |
|                                                                          |
|   Password:                                                              |
|   [ ************                                                     ]   |
|   (v) 10+ Characters    (v) Upper & Lowercase    (v) Number & Symbol     |
|                                                                          |
|   Confirm Password:                                                      |
|   [ ************                                                     ]   |
|                                                                          |
|   [                     Create Isolated Account                      ]   |
|                                                                          |
|                         Already registered? Log in                       |
+--------------------------------------------------------------------------+
```

- **User:** New Visitor / Prospective Account Owner.
- **Goal:** Provision a new account partition with cryptographically enforced password complexity.
- **Navigation:** Standalone clean card; link back to `/login`.
- **Inputs:**
  - `email`: Email input, type `email`.
  - `username`: Alphanumeric text input (3 to 50 characters).
  - `password`: Password input.
  - `confirm_password`: Password input.
- **Validation:**
  - Real-time password policy indicator checklist (10+ characters, uppercase, lowercase, numeric digit, special symbol - `SEC-002`).
  - Strict equality check between `password` and `confirm_password`.
- **Success Feedback:** *"Account created successfully. Please sign in to access your ledger."* Redirects to `/login`.
- **Error Feedback:** Inline field validation errors (e.g. *"Username already taken"*, *"Password must be at least 10 characters"*).
- **Authorization Considerations:** Unauthenticated endpoint; rate-limited by IP to prevent automated bot registrations (`SEC-003`).
- **Confidentiality Considerations:** Password fields masked; inputs cleared upon submission failure; no credential logging.
- **Secure Display Considerations:** Displays clear strength rules without revealing internal salt or hash specifics.

---

### 2.3 Screen 3: Dashboard / Monthly Summary (`/dashboard`)
- **Visual Wireframe:** [`docs/ui/screen3_dashboard.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen3_dashboard.svg)

```
+----------------------------------------------------------------------------------------------------+
|  S P E M A | SECURE EXPENSE           Dashboard   Transactions   Reports   Settings      (JD) Logout |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  October 2026 Overview                                      [ October 2026 v ]   [ + Add Transaction ]|
|  Personal financial summary scoped strictly to your account                                        |
|                                                                                                    |
|  +---------------------------+   +---------------------------+   +-------------------------------+ |
|  | TOTAL INCOME              |   | TOTAL EXPENSES            |   | NET CASH BALANCE              | |
|  | $5,400.00                 |   | $2,185.50                 |   | +$3,214.50                    | |
|  | +12% from last month      |   | 42 transactions logged    |   | Healthy savings margin (59.5%)| |
|  +---------------------------+   +---------------------------+   +-------------------------------+ |
|                                                                                                    |
|  +---------------------------------------+   +---------------------------------------------------+ |
|  | Spending by Category                  |   | Recent Activity                    View All (42) >| |
|  | Housing & Rent      $1,200.00 (54%)   |   | DATE        CATEGORY    DESCRIPTION        AMOUNT | |
|  | [====================               ] |   | 2026-10-07  Groceries   Organic Market    -$64.20 | |
|  | Groceries & Food      $485.50 (22%)   |   | 2026-10-05  Salary      Monthly Payroll+$5,400.00 | |
|  | [========                           ] |   | 2026-10-02  Rent        Apartment Lease -$1,200.00 | |
|  | Utilities & Bills     $280.00 (13%)   |   | 2026-10-01  Utilities   Internet & Power  -$145.00 | |
|  | [====                               ] |   +---------------------------------------------------+ |
|  +---------------------------------------+                                                         |
+----------------------------------------------------------------------------------------------------+
```

- **User:** Authenticated Account Owner.
- **Goal:** Comprehensive real-time view of personal monthly income, expenditures, net cash balance, and spending distribution.
- **Navigation:** Persistent navigation header (Dashboard, Transactions, Reports, Settings, Logout); Period dropdown; Quick action "+ Add Transaction".
- **Inputs:**
  - `period_selector`: Dropdown select (`Year-Month`).
- **Validation:** Year and month bounded between 2000 and current year + 1.
- **Success Feedback:** Live re-calculation of summary metrics and category progress bars upon period selection.
- **Error Feedback:** Non-intrusive warning banner if calculation fails.
- **Authorization Considerations:** **Zero-Trust Multi-Tenancy.** The server executes queries strictly using `WHERE user_id = :current_user.id`. The URL path contains NO client `user_id` parameter (e.g. `/dashboard`, never `/dashboard?user_id=1`).
- **Confidentiality Considerations:** All metrics reflect exclusively the authenticated user's records. Cached responses use `Cache-Control: no-store, private`.
- **Secure Display Considerations:** Tabular monospace digits for financial balance alignment; HTML entity escaping on all category labels.

---

### 2.4 Screen 4: Add Transaction (`/transactions/new`)
- **Visual Wireframe:** [`docs/ui/screen4_add_transaction.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen4_add_transaction.svg)

```
+----------------------------------------------------------------------------------------------------+
|  S P E M A | SECURE EXPENSE           Dashboard   Transactions   Reports   Settings      (JD) Logout |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|                       +----------------------------------------------------+                       |
|                       |  Record Transaction                                |                       |
|                       |  Permanently associated with your account session  |                       |
|                       |                                                    |                       |
|                       |  Transaction Type:                                 |                       |
|                       |  [ (o) Income (+) ]        [ ( ) Expense (-) ]     |                       |
|                       |                                                    |                       |
|                       |  Amount (USD):                                     |                       |
|                       |  [ $ 150.00                                      ] |                       |
|                       |                                                    |                       |
|                       |  Date:                     Category:               |                       |
|                       |  [ 2026-10-08            ] [ Consulting / Freelance]|                      |
|                       |                                                    |                       |
|                       |  Description / Notes (Optional, max 255 chars):    |                       |
|                       |  [ Q3 Security Architecture Review Milestone     ] |                       |
|                       |                                                    |                       |
|                       |  [ (i) Ownership is derived from verified token  ] |                       |
|                       |                                                    |                       |
|                       |  [ Save Transaction ]       [ Cancel ]             |                       |
|                       +----------------------------------------------------+                       |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

- **User:** Authenticated Account Owner.
- **Goal:** Record a new income or expense entry with categorization and optional notes.
- **Navigation:** Modal dialog or dedicated page; cancel returns to previous screen.
- **Inputs:**
  - `type`: Radio / Segmented toggle (`INCOME` / `EXPENSE`).
  - `amount`: Number input, formatted with 2 decimal places, step `0.01`.
  - `transaction_date`: Date input, default to today.
  - `category_id`: Select dropdown (system categories + caller's custom categories).
  - `description`: Text area, max length 255.
- **Validation:**
  - Amount must be > 0.00 and <= 1,000,000.00 (`SEC-008`).
  - Date must be a valid ISO date.
  - Category must be a non-empty selection.
  - Form has **NO hidden `<input name="user_id">`**.
- **Success Feedback:** Subtle notification toast: *"Transaction of $150.00 recorded successfully."* Redirects to updated dashboard/transaction list.
- **Error Feedback:** Inline field validation errors beneath invalid inputs (e.g. *"Amount must be greater than 0.00"*).
- **Authorization Considerations:** Identity is derived exclusively from the session token by the server. Any forged client parameters are discarded.
- **Confidentiality Considerations:** Financial amount and description inputs are transmitted over TLS 1.3; browser autocomplete for descriptions is configured to `off` to prevent cross-profile leakage on shared workstations.
- **Secure Display Considerations:** Description field undergoes context-aware HTML escaping upon rendering (`SEC-010`).

---

### 2.5 Screen 5: Transaction Search & List (`/transactions`)
- **Visual Wireframe:** [`docs/ui/screen5_transaction_list.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen5_transaction_list.svg)

```
+----------------------------------------------------------------------------------------------------+
|  S P E M A | SECURE EXPENSE           Dashboard   Transactions   Reports   Settings      (JD) Logout |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  Transaction History                                                        [ (v) Export Report ]  |
|  Search and filter your personal financial records                                                 |
|                                                                                                    |
|  +-----------------------------------------------------------------------------------------------+ |
|  | [ Q Search notes... ]  [ All Categories v ]  [ All Types v ]  [ 2026-10-01 to 10-31 ] [Filter]| |
|  +-----------------------------------------------------------------------------------------------+ |
|                                                                                                    |
|  +-----------------------------------------------------------------------------------------------+ |
|  | DATE        TYPE     CATEGORY    DESCRIPTION                       AMOUNT           ACTIONS   | |
|  | 2026-10-07  EXPENSE  Groceries   Organic Supermarket Fresh        -$64.20     [Edit] [Delete] | |
|  | 2026-10-05  INCOME   Salary      Corporate Monthly Payroll     +$5,400.00     [Edit] [Delete] | |
|  | 2026-10-02  EXPENSE  Housing     Apartment Monthly Lease        -$1,200.00     [Edit] [Delete] | |
|  +-----------------------------------------------------------------------------------------------+ |
|  Showing 1 to 3 of 42 records (Scoped strictly to current user)                       [ 1 ] [ 2 ] [>] |
+----------------------------------------------------------------------------------------------------+
```

- **User:** Authenticated Account Owner.
- **Goal:** Discover, filter, inspect, edit, and delete personal transactions.
- **Navigation:** "Transactions" tab in main navigation. Quick access to Export Report.
- **Inputs:**
  - `keyword`: Text input (alphanumeric search filter).
  - `category`: Select dropdown.
  - `type`: Select dropdown (`All`, `Income`, `Expense`).
  - `start_date` / `end_date`: Date range inputs.
  - `page`: Pagination control.
- **Validation:**
  - Search query validated against regex `^[a-zA-Z0-9_\-\s]*$` to prevent SQL injection probing.
  - Date range validated so `start_date <= end_date`.
- **Success Feedback:** Live table update with count indicator (*"Showing 1 to 3 of 42 records"*).
- **Error Feedback:** Empty state illustration: *"No transactions found matching your criteria. Try adjusting your filters."*
- **Authorization Considerations:**
  - **Tenancy Boundary:** Query executed with compound filter: `WHERE user_id = :current_user.id`.
  - **Row Actions (Edit/Delete):** Action links pass `transaction_id` in path. If a user tampers with the URL to reference another user's `transaction_id`, the server returns `HTTP 404 Not Found` (anti-enumeration).
- **Confidentiality Considerations:** Displays exclusively the records belonging to the authenticated account. No other user's names, emails, or transactions ever appear in autocomplete, search drops, or pagination totals.
- **Secure Display Considerations:** Destructive delete action requires confirmation modal with the exact transaction date and amount displayed to prevent accidental deletion.

---

### 2.6 Screen 6: Generate Financial Report (`/reports`)
- **Visual Wireframe:** [`docs/ui/screen6_generate_report.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen6_generate_report.svg)

```
+----------------------------------------------------------------------------------------------------+
|  S P E M A | SECURE EXPENSE           Dashboard   Transactions   Reports   Settings      (JD) Logout |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|                       +----------------------------------------------------+                       |
|                       |  Export Financial Report                           |                       |
|                       |  Download an auditable, formula-sanitized statement|                       |
|                       |                                                    |                       |
|                       |  Report Time Span:                                 |                       |
|                       |  [ October 2026 ] [ Last 3 Months ] [ Year to Date]|                       |
|                       |                                                    |                       |
|                       |  Transaction Types:                                |                       |
|                       |  [ Consolidated Ledger (Income & Expenses)       v]|                       |
|                       |                                                    |                       |
|                       |  File Format:                                      |                       |
|                       |  [ (o) CSV (Spreadsheet) ]    [ ( ) JSON (Audit) ] |                       |
|                       |                                                    |                       |
|                       |  +-----------------------------------------------+ |                       |
|                       |  | [!] Active Security Controls:                 | |                       |
|                       |  | * Zero-Trust: Scoped solely to current_user.id| |                       |
|                       |  | * Formula Immunity: =, +, -, @ sanitized      | |                       |
|                       |  +-----------------------------------------------+ |                       |
|                       |                                                    |                       |
|                       |  [ (v) Download Sanitized CSV ]    [ Cancel ]      |                       |
|                       +----------------------------------------------------+                       |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

- **User:** Authenticated Account Owner.
- **Goal:** Export filtered financial statements into CSV or JSON formats for offline tax preparation or personal budgeting.
- **Navigation:** "Reports" tab in main navigation.
- **Inputs:**
  - `period_range`: Preset buttons (`Current Month`, `Last 3 Months`, `Year to Date`, `Custom`).
  - `transaction_type`: Dropdown (`All`, `Income Only`, `Expense Only`).
  - `format`: Radio selector (`CSV` or `JSON`).
- **Validation:** Date ranges must not exceed 5 years to prevent memory exhaustion DoS (`SEC-017`).
- **Success Feedback:** Browser download begins immediately with progress notification: *"Personal Expense Report downloaded."*
- **Error Feedback:** Inline alert if no transactions match the selected period.
- **Authorization Considerations:** The export query is hardcoded to enforce `WHERE user_id = :current_user.id`. The user **cannot specify an account ID or tenant parameter** in the export request.
- **Confidentiality Considerations:** Downloaded file is generated dynamically in memory; temporary files are never saved in shared server directories (`/tmp`). Filename follows pattern `expense_report_<YYYYMMDD>.csv` without leaking usernames or system IDs.
- **Secure Display Considerations:** **Formula Injection Immunity (CWE-1236):** UI documentation informs the user that spreadsheet formula symbols are sanitized with a leading `'` to ensure safety in Microsoft Excel and LibreOffice Calc (`SEC-011`).

---

## 3. Application of UI Golden Rules

| Golden Rule | Practical UI Application in SPEMA | Security & Usability Benefit |
| :--- | :--- | :--- |
| **1. Consistency** | Uniform layout, header, typography, button treatments, and color semantics (`#2C4C3B` for positive income/actions, `#A64B2A` for expenses/destructions) across all 6 screens. | Reduces cognitive load; prevents user confusion regarding financial state and destructive operations. |
| **2. User Control** | Confirmation modals for transaction deletion; clear "Cancel" buttons on all forms; explicit session logout controls. | Prevents accidental financial ledger corruption; gives user total authority over their session lifecycle. |
| **3. Feedback** | Real-time password strength checklists on registration; toast notifications on transaction creation; non-blocking loading states during report generation. | Keeps user continuously informed of operation progress without leaking sensitive technical details. |
| **4. Error Prevention** | Strict input masking; currency inputs formatted automatically to two decimal places; disabled submit buttons until required fields are valid. | Prevents malformed data from reaching the backend, minimizing server-side validation rejections. |
| **5. Clear Navigation** | Single persistent navigation bar; breadcrumbs on deep screens; active tab underline indicator. | Eliminates ambiguous user orientation; ensures user can always return to Dashboard in one click. |
| **6. Visibility of System Status** | Summary totals prominently displayed on the dashboard; filter count badges on transaction list; active period indicator. | Guarantees user always knows exactly which date period and filter scope is currently being displayed. |

---

## 4. Strict Anti-Data Leakage Guidelines

To enforce the primary security mandate, the UI design adheres to eight non-negotiable anti-leakage rules:

1. **URLs:** No endpoint URL or browser route contains a `user_id` query parameter or path variable (e.g. `/transactions`, `/reports/export`, never `/users/42/transactions`).
2. **Search Results:** The transaction search view only receives and displays records belonging to the authenticated session.
3. **Error Messages:** System errors emit generic messages (`HTTP 500: An unexpected error occurred. Ref: <UUID>`), completely concealing database table names, SQL queries, or foreign key details.
4. **Reports:** CSV export streams solely caller records, with dangerous spreadsheet characters (`=`, `+`, `-`, `@`) neutralized.
5. **Summary Widgets:** Dashboard cards display aggregations calculated strictly from the caller's tenancy partition.
6. **Autocomplete:** Browser autocomplete is disabled (`autocomplete="off"` or `autocomplete="new-password"`) on sensitive credential inputs to prevent data retention on shared workstations.
7. **Transaction IDs:** Editing or deleting a transaction sends only `transaction_id`. If a user tampers with the ID to reference another user's record, the UI receives a uniform `HTTP 404 Not Found` rather than `403 Forbidden`, preventing identifier enumeration (`SEC-006`).
8. **Browser-Side State:** `localStorage` and `sessionStorage` strictly store the current user's ephemeral JWT token. No other user's records or cached financial statements are ever retained in client storage.

---

## 5. Traceability & Consistency Verification

| Screen | Phase 2 Requirements | Phase 3 Use Cases | Phase 4 DFD Processes | Phase 5 Architecture Components | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **1. Login** | `FR-002`, `SEC-001`, `SEC-003`, `SEC-004` | `UC-02: Login` | Process 1.0 (Auth) | `AuthService`, API Routers | **Consistent** |
| **2. Registration** | `FR-001`, `SEC-001`, `SEC-002` | `UC-01: Register` | Process 1.0 (Auth) | `AuthService`, `UserCreateDTO` | **Consistent** |
| **3. Dashboard** | `FR-007`, `NFR-003`, `SEC-005` | `UC-11: Summary` | Process 4.0 (Analysis) | `ReportingService`, `TransactionRepo` | **Consistent** |
| **4. Add Transaction** | `FR-004`, `FR-005`, `FR-006`, `SEC-008`| `UC-04`, `UC-05`, `UC-TXN-01` | Process 3.0 (Txn) | `TransactionService`, Validation | **Consistent** |
| **5. Search & List** | `FR-008`, `FR-009`, `SEC-005`, `SEC-006`| `UC-07`, `UC-08`, `UC-09`, `UC-10` | Process 3.0 (Txn) | `TransactionRepo`, Anti-Enumeration | **Consistent** |
| **6. Generate Report** | `FR-010`, `SEC-011`, `SEC-012` | `UC-12: Report`, `UC-REP-01` | Process 5.0 (Reports) | `ReportingService`, `SecureCSVExporter`| **Consistent** |

---

## 6. Phase 6 Laboratory Artifact Summary

### 6.1 Artifacts Created & Stored
1. **Primary Laboratory Documentation:**  
   [`docs/phases/phase-06-ui.md`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/phases/phase-06-ui.md)
2. **Visual SVG Wireframe Mockups (under `docs/ui/`):**  
   - Screen 1 (Login): [`docs/ui/screen1_login.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen1_login.svg)
   - Screen 2 (Registration): [`docs/ui/screen2_register.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen2_register.svg)
   - Screen 3 (Dashboard / Monthly Summary): [`docs/ui/screen3_dashboard.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen3_dashboard.svg)
   - Screen 4 (Add Transaction): [`docs/ui/screen4_add_transaction.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen4_add_transaction.svg)
   - Screen 5 (Transaction Search & List): [`docs/ui/screen5_transaction_list.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen5_transaction_list.svg)
   - Screen 6 (Generate Financial Report): [`docs/ui/screen6_generate_report.svg`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/docs/ui/screen6_generate_report.svg)

### 6.2 Upstream Dependencies
- Consumes **Rugged Agile design principles** from Phase 1 (`docs/phases/phase-01-agile.md`).
- Maps directly to **`FR-001` - `FR-012` and `SEC-001` - `SEC-018`** from Phase 2 (`docs/phases/phase-02-requirements.md`).
- Implements the **Use Case Specifications (`UC-TXN-01`, `UC-REP-01`)** from Phase 3 (`docs/phases/phase-03-uml.md`).
- Honors the **DFD boundaries and sensitive data flows** from Phase 4 (`docs/phases/phase-04-data-flow.md`).
- Matches the **Presentation layer and Pydantic DTO boundaries** from Phase 5 (`docs/phases/phase-05-architecture.md`).

### 6.3 Downstream Hand-Off
- **Phase 7 (Threat Modeling & STRIDE):** Will analyze user input fields and web views for XSS, CSRF, and injection vectors.
- **Phase 8 (Attack Tree Analysis):** Will evaluate UI attack paths (credential stuffing on login, IDOR via search tampering).
- **Phase 12 (Secure Coding):** Will implement the Jinja2 templates and frontend forms following these exact wireframe layouts and security controls.
