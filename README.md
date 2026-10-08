# Secure Personal Expense Management Application (SPEMA)

[![CI Build](https://github.com/Thuriaanandh/Secure-Personal-Expense-Management/actions/workflows/ci.yml/badge.svg)](https://github.com/Thuriaanandh/Secure-Personal-Expense-Management/actions)
[![Security SAST](https://img.shields.io/badge/Bandit%20SAST-0%20Issues-brightgreen.svg)](bandit.yaml)
[![Tests Passing](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](pyproject.toml)

> **24CYS401 Secure Software Engineering Laboratory Examination**  
> A production-grade, zero-trust personal financial ledger built with rigorous security engineering principles and complete SSDLC traceability.

---

## 1. Primary Security Mandate

> *"An authenticated user must not be able to access, modify, search, aggregate or report on another user's financial records."*

In SPEMA, user tenancy is strictly enforced at every architecture boundary:
1. **Server-Derived Identity:** Client-supplied user identifiers (`user_id`) in payloads or query strings are strictly stripped and rejected (`extra = "forbid"` via Pydantic). Authenticated identity is resolved exclusively through verified cryptographic JWT claims via FastAPI's `Depends(get_current_active_user)`.
2. **Compound Query Scoping:** Every database repository query is programmatically scoped to the authenticated caller:
   $$\text{SELECT / UPDATE / DELETE} \quad \dots \quad \text{WHERE } id = :id \text{ AND } user\_id = :authenticated\_user\_id$$
3. **Anti-Enumeration Defense (CWE-200 / SEC-006):** Attempting to access, modify, or delete another user's transaction returns a uniform `HTTP 404 Not Found` rather than `403 Forbidden`, preventing identifier enumeration attacks.
4. **Formula Injection Neutralization (CWE-1236 / SEC-011):** All exported spreadsheet cells beginning with `=`, `+`, `-`, `@`, `\t`, or `\r` are sanitized by prepending a single quote (`'`).
5. **Session Revocation (SEC-004):** Logout deterministically revokes the JWT token's `jti` in a dedicated server-side blocklist database table.

---

## 2. Architecture & Design Principles

SPEMA implements a **Modular Monolith** using **Layered Clean Architecture**:

```
+-------------------------------------------------------------------------+
|                         Presentation Layer                              |
|   Jinja2 Minimalist UI (HTML5 / CSS3)  |  RESTful API Routers (/api/v1) |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                          Service Layer                                  |
|   AuthService  |  TransactionService  |  ReportingService  | AuditService |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                        Repository Layer                                 |
|   UserRepository  |  TransactionRepository  |  CategoryRepository       |
|          (MANDATORY user_id filter parameter on all methods)             |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                       Data Persistence Layer                            |
|        SQLAlchemy ORM Models  |  SQLite / PostgreSQL Database           |
+-------------------------------------------------------------------------+
```

---

## 3. Technology Stack

- **Backend Runtime:** Python 3.12, FastAPI 0.115, Uvicorn
- **ORM & Database:** SQLAlchemy 2.0, SQLite (Dev/Test) / PostgreSQL (Prod)
- **Cryptography & Security:** Argon2id (`passlib[argon2]`, `argon2-cffi`), HMAC-SHA256 JWT (`python-jose`)
- **Validation:** Pydantic 2.10 with strictly sealed schemas
- **Frontend:** Jinja2 server-rendered templates styled with warm editorial typography
- **Quality & SAST Gates:** Pytest 8.3, Bandit 1.9, Ruff 0.16, Custom Secret Scanner

---

## 4. Getting Started

### Prerequisites
- Python 3.11+ (Python 3.12 recommended)
- Git

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/Thuriaanandh/Secure-Personal-Expense-Management.git
   cd Secure-Personal-Expense-Management
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install pinned dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

---

## 5. Running the Application

Start the local development server:
```bash
uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
- **Web UI:** [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- **API Documentation:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **Health Checks:** [http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)

---

## 6. Security & Quality Verification

Run the full automated test suite (17 passed):
```bash
pytest -v tests/
```

Run Bandit Static Application Security Testing (SAST):
```bash
bandit -c bandit.yaml -r src/
```

Run Ruff code quality and style checks:
```bash
ruff check src/ tests/
```

Run automated secret scanner and git hygiene check:
```bash
python scripts/security_check.py
```

Execute unified reproducible build script (Windows PowerShell):
```powershell
.\scripts\build.ps1
```

---

## 7. SSDLC Phase Traceability Matrix

| Phase | Description | Key Deliverables | Status |
| :---: | :--- | :--- | :---: |
| **01** | Agile Process Engineering | Rugged Scrum & XP, Manifesto Mapping | Approved |
| **02** | Requirements Engineering | 12 FRs, 7 NFRs, 18 SEC requirements, CIA Matrix | Approved |
| **03** | Requirements Analysis & UML | Use Cases, Robustness Analysis, StarUML `.mdj` | Approved |
| **04** | Data & Information Flow Modeling | Relational ER Model, DFD Levels 0, 1, 2 | Approved |
| **05** | Architecture & Design Engineering | Modular Monolith, Layered Architecture, Security Blueprint | Approved |
| **06** | User Interface Design | 6 Minimalist Editorial Wireframes & Anti-Leakage Rules | Approved |
| **07** | Threat Modeling & STRIDE | Asset Inventory, 11 STRIDE Threats, 6 Vulnerability Dockets | Approved |
| **08** | Attack Tree & Refinement | Root Goal Attack Tree, 7-Pillar Security Architecture | Approved |
| **09** | Backlog & Scrum Planning | Jira Epics, User Stories, Acceptance Criteria | Completed |
| **10** | Sprint Execution & Metrics | Sprint Burndown, Velocity, Quality Metrics | Completed |
| **11** | Secure Build & CI/CD Baseline | Production Code, 17 Tests, SAST, CI/CD, Git Tag `v1.0.0` | **Complete** |

---

## 8. License

This project is submitted for academic assessment under the 24CYS401 Secure Software Engineering course curriculum.
