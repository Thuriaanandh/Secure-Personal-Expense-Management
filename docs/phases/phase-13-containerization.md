# Phase 13: Containerization and Kubernetes Deployment

**Project:** Secure Personal Expense Management Application (SPEMA)  
**Curriculum:** 24CYS401 Secure Software Engineering Laboratory  
**Document Version:** 1.2.0  
**Status:** Approved & Verified  
**Release Tag:** `v1.2.0`  

---

## 1. Executive Summary & Objectives

Phase 13 delivers a production-grade, hardened containerization and Kubernetes orchestration baseline for SPEMA. Conforming to SSDLC guidelines and defense-in-depth principles, the application is packaged into an unprivileged, minimal container and deployed to a local Kubernetes (Minikube) cluster with strict security controls.

---

## 2. Docker Security Architecture & Hardening

The production container image adheres to the following security controls:

1. **Minimal Base Image:** Uses `python:3.12-slim-bookworm` to minimize vulnerabilities and attack surface.
2. **Multi-Stage Build Pipeline:** Build tools and compiler caches remain in the intermediate `builder` stage, ensuring the final runtime contains only essential binaries and runtime packages.
3. **Dedicated Unprivileged User:** Runs as non-root user `appuser` (UID 10001, GID 10001, shell `/sbin/nologin`).
4. **No Baked Secrets:** Application secrets (`SECRET_KEY`, database credentials) are injected strictly via environment variables or Kubernetes Secrets.
5. **Strict `.dockerignore`:** Excludes development environments, Git history, local database files (`spema_ledger.db`), testing caches, and secret files.
6. **Strict Dependency Pinning:** Dependencies are installed from pinned `requirements.txt` with `--no-cache-dir`.
7. **Native Docker Healthcheck:** Configured with `HEALTHCHECK` periodically probing `/healthz`.
8. **Read-Only Root Filesystem Ready:** Distinct directory hierarchy (`/data` for persistent database, `/tmp` for temporary files) allowing the container to execute under `readOnlyRootFilesystem: true`.

---

## 3. Kubernetes Orchestration & Security Architecture

The application is deployed to Kubernetes in the `spema` namespace with declarative manifests under `k8s/`:

```
k8s/
├── namespace.yaml         # Enforces Pod Security Standard 'restricted'
├── secret.yaml            # Opaque secret for HMAC-SHA256 JWT signing key
├── configmap.yaml         # Non-sensitive runtime settings
├── pvc.yaml               # 500Mi PersistentVolumeClaim for ledger storage
├── deployment.yaml        # Single-replica hardened deployment with probes & securityContext
├── service.yaml           # NodePort service exposing port 8000 on nodePort 30080
├── networkpolicy.yaml     # Restricts ingress and egress network traffic
└── kustomization.yaml     # Declarative deployment bundling
```

### 3.1 Security Context Verification

- **Namespace Restriction:** `pod-security.kubernetes.io/enforce: restricted`
- **Pod Security Context:**
  - `runAsNonRoot: true`
  - `runAsUser: 10001`
  - `runAsGroup: 10001`
  - `fsGroup: 10001`
  - `seccompProfile.type: RuntimeDefault`
- **Container Security Context:**
  - `allowPrivilegeEscalation: false`
  - `readOnlyRootFilesystem: true`
  - `capabilities.drop: ["ALL"]`
- **Liveness & Readiness Probes:**
  - Liveness probe: HTTP `GET /healthz`
  - Readiness probe: HTTP `GET /readyz`
- **Resource Limits:**
  - Requests: CPU `100m`, Memory `128Mi`
  - Limits: CPU `500m`, Memory `256Mi`
- **Persistence:** Volume mount at `/data` backed by PersistentVolumeClaim guarantees ledger data persistence across pod restarts while maintaining root filesystem immutability.

---

## 4. Verification Evidence

### 4.1 Docker Build & Verification
```
Step 20/20 : CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
Successfully built 41d27ab124bd
Successfully tagged spema:1.2.0
Successfully tagged spema:latest

# Health Probe Verification
HTTP/1.1 200 OK
{"status":"healthy","service":"Secure Personal Expense Management Application","version":"1.1.0"}

# Non-Root User Verification
uid=10001(appuser) gid=10001(appgroup) groups=10001(appgroup)
```

### 4.2 Kubernetes Manifest Validation
```
namespace/spema configured (server dry run)
configmap/spema-config created (server dry run)
secret/spema-secret created (server dry run)
service/spema-service created (server dry run)
persistentvolumeclaim/spema-data-pvc created (server dry run)
deployment.apps/spema-deployment created (server dry run)
networkpolicy.networking.k8s.io/spema-network-policy created (server dry run)
```

### 4.3 Minikube Deployment & Pod Health
```
NAME                                   READY   STATUS    RESTARTS   AGE
pod/spema-deployment-8d79457d5-7hjzc   1/1     Running   0          80s

NAME                    TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/spema-service   NodePort   10.100.153.37   <none>        8000:30080/TCP   80s

NAME                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES
persistentvolumeclaim/spema-data-pvc   Bound    pvc-92e9a8ad-36ee-43c0-8ded-27d25188672c   500Mi      RWO
```

### 4.4 Security Controls Runtime Proof
```
# 1. Non-root user in Pod:
$ kubectl exec -n spema spema-deployment-8d79457d5-7hjzc -- id
uid=10001(appuser) gid=10001(appgroup) groups=10001(appgroup)

# 2. Read-only root filesystem enforcement:
$ kubectl exec -n spema spema-deployment-8d79457d5-7hjzc -- touch /root_test
touch: cannot touch '/root_test': Read-only file system
command terminated with exit code 1

# 3. Persistent writable storage on /data:
$ kubectl exec -n spema spema-deployment-8d79457d5-7hjzc -- ls -la /data
-rw-r--r-- 1 appuser appgroup 98304 Oct  8 09:10 spema_ledger.db
```

### 4.5 End-to-End Service Reachability & API Execution
```
[*] Testing SPEMA Kubernetes Service at http://192.168.49.2:30080...
[+] Healthcheck passed: {'status': 'healthy', 'service': 'Secure Personal Expense Management Application', 'version': '1.1.0'}
[*] User already registered, continuing to login...
[+] User login succeeded, JWT token obtained (length 249)
[+] Categories retrieved: 9 categories found.
    Selected Category: id=1, name=Salary
[+] Transaction created successfully: id=3, amount=4500.00
[+] Summary report retrieved: total_income=13500.00, net_savings=13500.00

[SUCCESS] Complete Kubernetes Deployment & API Workflow Verified Successfully!
```

---

## 5. Traceability Matrix

| Requirement / Standard | Implementation | Evidence |
| :--- | :--- | :--- |
| **Docker Security (Base Image)** | `python:3.12-slim-bookworm` | Multi-stage Dockerfile |
| **Docker Security (Non-Root)** | `appuser` (UID 10001) | `id` inside container verified |
| **Docker Security (Healthcheck)** | Docker `HEALTHCHECK` on `/healthz` | Container status `healthy` |
| **Docker Security (No Secrets)** | Environment / Secret injection | Zero credentials in image |
| **K8s Security (Context)** | `readOnlyRootFilesystem: true`, `drop: [ALL]` | `touch /root_test` denied |
| **K8s Security (Probes)** | `/healthz` (liveness) & `/readyz` (readiness) | Pod status `1/1 Running` |
| **K8s Security (Secrets/Config)** | `ConfigMap` + `Secret` separated | Pod logs & env verified |
| **K8s Persistence** | `PersistentVolumeClaim` at `/data` | Durable SQLite transactions |
