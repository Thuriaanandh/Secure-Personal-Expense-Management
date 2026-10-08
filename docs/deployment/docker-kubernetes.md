# Docker and Kubernetes Deployment Guide

**Project:** Secure Personal Expense Management Application (SPEMA)  
**Document Version:** 1.2.0  
**Target Environments:** Production Docker, Kubernetes, Local Minikube  

---

## 1. Containerization Architecture

SPEMA is packaged using a multi-stage, production-hardened Dockerfile adhering to zero-trust principles and container security best practices.

### 1.1 Docker Security Controls Implemented

| Security Control | Implementation Detail | Rationale / Benefit |
| :--- | :--- | :--- |
| **Minimal Base Image** | `python:3.12-slim-bookworm` | Minimizes attack surface, eliminates unnecessary binaries and compilers. |
| **Multi-Stage Build** | Separate `builder` and `runner` stages | Strips wheel caches, gcc, and build utilities from runtime layer. |
| **Dedicated Non-Root User** | `appuser:appgroup` (UID: 10001, GID: 10001) | Eliminates root privileges inside the container (`/sbin/nologin`). |
| **No Baked Secrets** | Runtime injection via environment / Secrets | Prevents credential leakage through image layers or registries. |
| **Strict `.dockerignore`** | Excludes `.git`, `.env*`, `*.db`, tests, docs | Prevents leaking sensitive developer secrets, tests, or state. |
| **Strict Dependency Control** | `pip install --no-cache-dir -r requirements.txt` | Pins exact package versions and avoids stale cache vulnerabilities. |
| **Native Docker Healthcheck** | Periodic probe on `http://localhost:8000/healthz` | Automatic health tracking and container restart on hung workers. |
| **Read-Only Root Filesystem Ready** | Volume mount points at `/data` and `/tmp` | Supports immutable rootfs execution (`readOnlyRootFilesystem: true`). |

---

## 2. Docker Build and Run Instructions

### 2.1 Build the Image
```bash
docker build -t spema:1.2.0 -t spema:latest .
```

### 2.2 Run in Standalone Docker (with Persistent Volume)
```bash
# Create local volume for ledger persistence
docker volume create spema-data

# Run container with injected secrets and non-root execution
docker run -d \
  --name spema-app \
  -p 8000:8000 \
  -e APP_ENV="production" \
  -e SECRET_KEY="your-minimum-32-characters-cryptographic-secret-key-here" \
  -e DATABASE_URL="sqlite:////data/spema_ledger.db" \
  -v spema-data:/data \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  spema:1.2.0
```

### 2.3 Verify Health and Security
```bash
# Verify container is running and healthy
docker ps -f name=spema-app

# Probe health endpoint
curl -i http://localhost:8000/healthz

# Verify unprivileged user inside container
docker exec spema-app id
# Output: uid=10001(appuser) gid=10001(appgroup) groups=10001(appgroup)
```

---

## 3. Kubernetes Architecture & Manifests

All Kubernetes resources are isolated in the `spema` namespace under `k8s/`:

```
k8s/
├── namespace.yaml         # Dedicated namespace with Pod Security Standard 'restricted'
├── secret.yaml            # Opaque secret for JWT signing keys
├── configmap.yaml         # Environment configuration (APP_ENV, DB URL, rate limits)
├── pvc.yaml               # 500Mi PersistentVolumeClaim for SQLite database storage
├── deployment.yaml        # Hardened single-replica Deployment with probes and securityContext
├── service.yaml           # NodePort service exposing port 8000 on nodePort 30080
├── networkpolicy.yaml     # Restricts ingress to port 8000 and egress to DNS/HTTPS
└── kustomization.yaml     # Declarative deployment bundling
```

### 3.1 Kubernetes Security Hardening Profile

- **Pod Security Standard Restricted:** The `spema` namespace enforces `pod-security.kubernetes.io/enforce: restricted`.
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
- **Resource Constraints:**
  - CPU requests: `100m`, limits: `500m`
  - Memory requests: `128Mi`, limits: `256Mi`
- **Probes:**
  - Liveness: HTTP `GET /healthz` (initial delay: 10s, period: 15s)
  - Readiness: HTTP `GET /readyz` (initial delay: 5s, period: 10s)
- **Secrets Management:** Injected from `spema-secret` using `secretRef` and decoupled from application code.

---

## 4. Minikube Deployment and Verification

### 4.1 Deploying to Minikube
```bash
# 1. Start Minikube (using docker driver)
minikube start --driver=docker --memory=2048mb --cpus=2

# 2. Load the built image into Minikube
minikube image load spema:1.2.0

# 3. Apply manifests using Kustomize
kubectl apply -k k8s/

# 4. Check rollout status
kubectl rollout status deployment/spema-deployment -n spema
```

### 4.2 Verifying Deployment
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Test service endpoint
curl -i http://${MINIKUBE_IP}:30080/healthz
curl -i http://${MINIKUBE_IP}:30080/readyz

# Run end-to-end integration verification suite
python3 scripts/test_k8s_deployment.py
```
