# Secure Deployment Checklist

**Project:** Secure Personal Expense Management Application (SPEMA)  
**Curriculum:** 24CYS401 Secure Software Engineering Laboratory  
**Document Version:** 1.4.0  
**Status:** Approved & Verified  
**Release Tag:** `v1.4.0`  

---

## 1. Overview & Scope

This checklist defines mandatory security controls and verification criteria for deploying the Secure Personal Expense Management Application (SPEMA) to production. Every item must be validated before promoting images to staging or production environments.

The automated audit script [`scripts/verify_deployment.py`](file:///C:/Users/anand/OneDrive/Documents/SSDLC/endsem_lab/scripts/verify_deployment.py) programmatically asserts each control prior to release.

---

## 2. Production Deployment Security Checklist

| Category | Control ID | Security Control Description | Verification Method | Status |
|---|---|---|---|:---:|
| **Secrets** | SEC-CHK-01 | Cryptographic secret key (`SECRET_KEY`) has minimum length of 32 characters and high entropy. | Dynamic validation in `get_settings()` | **VERIFIED** |
| | SEC-CHK-02 | Zero hardcoded credentials or API tokens committed in source code or version control. | Automated scan via `scripts/security_check.py` | **VERIFIED** |
| | SEC-CHK-03 | Application secrets injected dynamically via Kubernetes Secrets or ambient environment variables. | Manifest audit in `k8s/secret.yaml` | **VERIFIED** |
| **Database** | DB-CHK-01 | Database stored on dedicated persistent volume (`/data`) separate from root filesystem. | `k8s/pvc.yaml` & `k8s/deployment.yaml` | **VERIFIED** |
| | DB-CHK-02 | Database engine enforces Write-Ahead Logging (WAL) and foreign key referential integrity. | SQLAlchemy connection parameters & SQLite PRAGMA | **VERIFIED** |
| | DB-CHK-03 | Least-privilege file permissions on SQLite ledger file (`chmod 0750 /data`). | Dockerfile runtime permissions | **VERIFIED** |
| **Authentication** | AUTH-CHK-01 | Passwords hashed using Argon2id with memory-hard parameters (`t=3, m=65536, p=4`). | `src/app/core/security.py` | **VERIFIED** |
| | AUTH-CHK-02 | NIST SP 800-63B compliant password complexity (minimum 10 chars, upper, lower, digit, special). | `validate_password_strength()` unit tests | **VERIFIED** |
| | AUTH-CHK-03 | Sliding-window rate limiter blocks brute-force authentication (>5 failures / 15 minutes). | `tests/security/test_auth_rate_limit.py` | **VERIFIED** |
| | AUTH-CHK-04 | Server-side token revocation store invalidates JWTs immediately upon user logout. | `tests/security/test_auth_failures_and_tokens.py` | **VERIFIED** |
| **Authorization** | AUTHZ-CHK-01| Server-side tenant scoping (`WHERE user_id = :uid`) on all ledger queries. Client `user_id` ignored. | `tests/security/test_idor_authorization.py` | **VERIFIED** |
| | AUTHZ-CHK-02| Uniform `HTTP 404 Not Found` response on missing or foreign tenant transactions (zero ID enumeration). | BOLA / IDOR test suite | **VERIFIED** |
| | AUTHZ-CHK-03| Default system categories protected against modification and deletion (`HTTP 403 Forbidden`). | `tests/security/test_category_authz.py` | **VERIFIED** |
| **Logging** | LOG-CHK-01 | Structured JSON security event logging emitted to standard output for SIEM ingestion. | `src/app/core/logging.py` | **VERIFIED** |
| | LOG-CHK-02 | Strict sensitive data redaction filter masks passwords, tokens, keys, and authorization headers (CWE-532). | `test_structured_security_logging_redaction` | **VERIFIED** |
| | LOG-CHK-03 | Unique `X-Correlation-ID` header injected on all requests and response error envelopes. | `SecurityHeadersMiddleware` | **VERIFIED** |
| **Monitoring** | MON-CHK-01 | Prometheus metrics exposition endpoint (`/metrics`) tracks auth failures, IDOR attempts, and error rates. | `GET /metrics` | **VERIFIED** |
| | MON-CHK-02 | Operational JSON metrics summary endpoint (`/api/v1/metrics`) provides health statistics. | `GET /api/v1/metrics` | **VERIFIED** |
| | MON-CHK-03 | Automated health probes (`/healthz`) and readiness probes (`/readyz`) validate application state. | Kubernetes liveness/readiness probes | **VERIFIED** |
| **HTTPS / TLS** | TLS-CHK-01 | HTTP Strict Transport Security (HSTS) header configured (`max-age=31536000; includeSubDomains; preload`). | `SecurityHeadersMiddleware` | **VERIFIED** |
| | TLS-CHK-02 | Session cookies configured with `HttpOnly=True`, `SameSite=lax`, and `Secure=True` in production. | `SESSION_COOKIE_SECURE` configuration | **VERIFIED** |
| | TLS-CHK-03 | Defense-in-depth OWASP security headers enforced (CSP, X-Frame-Options, X-Content-Type-Options, COOP, CORP). | `test_security_hardening_headers` | **VERIFIED** |
| **Container** | CONT-CHK-01| Container image built from minimal hardened base image (`python:3.12-slim-bookworm`). | `Dockerfile` | **VERIFIED** |
| | CONT-CHK-02| Container executes under dedicated unprivileged non-root user `appuser` (UID: 10001, GID: 10001). | `USER 10001:10001` in Dockerfile | **VERIFIED** |
| | CONT-CHK-03| Multi-stage build strips compilers, package managers, and development tooling from final image. | Dockerfile builder pattern | **VERIFIED** |
| | CONT-CHK-04| Native Docker `HEALTHCHECK` periodically queries `/healthz`. | Dockerfile HEALTHCHECK directive | **VERIFIED** |
| **Kubernetes** | K8S-CHK-01 | Deployment enforces Pod Security Standard `restricted` profile in namespace. | `k8s/namespace.yaml` | **VERIFIED** |
| | K8S-CHK-02 | Pod securityContext enforces `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, capabilities dropped (`ALL`).| `k8s/deployment.yaml` | **VERIFIED** |
| | K8S-CHK-03 | Resource requests and limits defined (CPU: 100m–500m, Memory: 128Mi–256Mi) preventing noisy neighbor DoS. | `k8s/deployment.yaml` | **VERIFIED** |
| | K8S-CHK-04 | NetworkPolicy restricts ingress to port 8000 and limits egress. | `k8s/networkpolicy.yaml` | **VERIFIED** |
| **CI / CD** | CI-CHK-01  | Central GitHub Actions pipeline executes 13 automated quality, security, and testing stages. | `.github/workflows/ci.yml` | **VERIFIED** |
| | CI-CHK-02  | Automated dependency vulnerability auditing (`pip-audit`) blocks deployment on known CVEs. | Pipeline Stage 3 | **VERIFIED** |
| | CI-CHK-03  | Static Application Security Testing (`bandit`) and linting (`ruff`) block build on security flaws. | Pipeline Stages 5 & 6 | **VERIFIED** |
| | CI-CHK-04  | 50 automated tests (unit, integration, API, security, property-based fuzzing) pass before release. | Pytest Automated Test Suite | **VERIFIED** |
| **Recovery** | REC-CHK-01 | Persistent volume claims (`spema-data-pvc`) ensure ledger survival across pod restarts. | `k8s/pvc.yaml` | **VERIFIED** |
| | REC-CHK-02 | Disaster recovery ledger snapshot procedure defined with RPO < 1 hour and RTO < 15 minutes. | Documented recovery procedures below | **VERIFIED** |

---

## 3. Disaster Recovery and Ledger Backup Procedures

### 3.1 Backup Strategy (RPO < 1 hour)

1. **Kubernetes Volume Snapshot:**
   ```bash
   kubectl create -f - <<EOF
   apiVersion: snapshot.storage.k8s.io/v1
   kind: VolumeSnapshot
   metadata:
     name: spema-ledger-snapshot-$(date +%Y%m%d%H%M)
     namespace: spema
   spec:
     volumeSnapshotClassName: csi-hostpath-snapclass
     source:
       persistentVolumeClaimName: spema-data-pvc
   EOF
   ```

2. **Automated SQLite Online Hot-Backup:**
   The SQLite Write-Ahead Log (WAL) allows non-blocking atomic online backups:
   ```bash
   kubectl exec -n spema deploy/spema-deployment -c spema -- \
     sqlite3 /data/spema_ledger.db ".backup '/data/backup_ledger_$(date +%Y%m%d%H%M).db'"
   ```

### 3.2 Restoration Strategy (RTO < 15 minutes)

1. Scale down deployment:
   ```bash
   kubectl scale deployment spema-deployment -n spema --replicas=0
   ```
2. Restore ledger file from backup snapshot onto persistent volume `/data`.
3. Verify file permissions: `chown 10001:10001 /data/spema_ledger.db && chmod 0600 /data/spema_ledger.db`.
4. Scale deployment back up:
   ```bash
   kubectl scale deployment spema-deployment -n spema --replicas=1
   ```
5. Execute automated audit: `python scripts/verify_deployment.py`.

---

## 4. Automated Verification Execution Result

```text
======================================================================
SPEMA Secure Deployment Verification Audit (v1.4.0)
======================================================================

[Check 1/11] Auditing Secrets & Configuration...
  [+] SECRET_KEY length >= 32 chars: OK

[Check 2/11] Auditing Database Configuration...
  [+] DATABASE_URL dialect configured: sqlite OK

[Check 3/11] Auditing Authentication System...
  [+] User Registration Endpoint: OK
  [+] Authentication & JWT Issuance: OK

[Check 4/11] Auditing Tenant Isolation & IDOR Protection...
  [+] Server-side Tenant Scoping (Uniform 404 IDOR immunity): OK

[Check 5/11] Auditing Structured Security Logging & Redaction...
  [+] Sensitive Field Redaction Filter: OK
  [+] In-Memory Security Audit Events Captured: 3 events OK

[Check 6/11] Auditing Monitoring & Metrics Endpoints...
  [+] Prometheus /metrics exposition: OK
  [+] JSON /api/v1/metrics summary: OK

[Check 7/11] Auditing OWASP Security Headers & HSTS...
  [+] All OWASP Security Headers & HSTS & Correlation IDs: OK

[Check 8/11] Auditing Container Dockerfile Hardening...
  [+] Multi-stage build, non-root user (10001), HEALTHCHECK: OK

[Check 9/11] Auditing Kubernetes Manifests...
  [+] PSS Restricted, readOnlyRootFilesystem, runAsNonRoot: OK

[Check 10/11] Auditing CI/CD Workflow...
  [+] CI/CD Pipeline 13 stages with SAST, audit, and testing gates: OK

[Check 11/11] Auditing Health & Readiness Probes...
  [+] /healthz and /readyz probes responsive: OK

======================================================================
[SUCCESS] All 14/14 Deployment Checks Passed!
The SPEMA system is verified ready for production deployment.
======================================================================
```
