# ==============================================================================
# SPEMA Production-Hardened Multi-Stage Dockerfile
# Security Controls Implemented:
#   1. Minimal Base Image: python:3.12-slim-bookworm
#   2. Multi-Stage Build: Build tooling stripped from final runtime image
#   3. Dedicated Non-Root User: appuser (UID 10001, GID 10001, /sbin/nologin)
#   4. No Baked Secrets: Configurations injected strictly via Environment / K8s Secrets
#   5. Strict Dependency Pinning: requirements.txt with --no-cache-dir
#   6. Native Docker Healthcheck: Automated HTTP probe on /healthz
#   7. Read-Only Filesystem Ready: Dedicated volume mount points for /data and /tmp
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Prevent bytecode caching and enable unbuffered output during build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pinned production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Hardened Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# Metadata
LABEL maintainer="Secure Software Engineering Team <security@spema.local>" \
      description="Production image for Secure Personal Expense Management Application" \
      version="1.3.0" \
      security.scanned="true"

# Runtime Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    APP_ENV="production" \
    DATABASE_URL="sqlite:////data/spema_ledger.db"

# Install minimal essential runtime packages and clean package manager cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create dedicated unprivileged group and user (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /app appuser

# Create necessary application, storage, and runtime directories
WORKDIR /app
RUN mkdir -p /app /data /tmp && \
    chown -R appuser:appgroup /app /data /tmp && \
    chmod 750 /app /data && \
    chmod 777 /tmp

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application source code
COPY --chown=appuser:appgroup src/ /app/src/

# Drop privileges to non-root user
USER 10001:10001

# Expose internal application port
EXPOSE 8000

# Container Healthcheck (verifies application responsiveness via /healthz endpoint)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f -s http://localhost:8000/healthz || exit 1

# Launch ASGI production server
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
