import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.app.core.config import get_settings
from src.app.core.database import init_db
from src.app.core.logging import log_security_event
from src.app.core.metrics import metrics
from src.app.routers import auth, categories, health, reports, transactions, web
from src.app.routers import metrics as metrics_router

# Configure logger
logger = logging.getLogger("spema")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    settings = get_settings()
    logger.info("Initializing SPEMA database schemas...")
    init_db()
    logger.info(
        f"SPEMA {settings.APP_VERSION} initialized successfully in {settings.APP_ENV} mode."
    )
    # Emit structured security baseline event
    log_security_event(
        event_type="SECURITY_CONFIG",
        action="APPLICATION_STARTUP",
        status_code=200,
        resource="system:kernel",
        details={
            "app_version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "algorithm": settings.ALGORITHM,
            "token_ttl_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "rate_limit_max_attempts": settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
            "rate_limit_window_seconds": settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
            "hsts_enabled": settings.SECURE_HSTS_SECONDS > 0,
            "hsts_seconds": settings.SECURE_HSTS_SECONDS,
            "session_cookie_secure": settings.SESSION_COOKIE_SECURE,
            "cors_origins_count": len(settings.CORS_ORIGINS),
        },
    )
    yield
    # Shutdown
    log_security_event(
        event_type="SECURITY_CONFIG",
        action="APPLICATION_SHUTDOWN",
        status_code=200,
        resource="system:kernel",
        details={"status": "clean_shutdown"},
    )
    logger.info("SPEMA shutting down cleanly.")


# Initialize FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Secure Personal Expense Management Application — 24CYS401 SSDLC Baseline",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)


# 1. Security Headers & Correlation ID Middleware (OWASP Secure Headers Project)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract or generate request correlation ID for end-to-end tracing
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Enforce HSTS (Strict-Transport-Security)
        if settings.SECURE_HSTS_SECONDS > 0:
            hsts_val = f"max-age={settings.SECURE_HSTS_SECONDS}; includeSubDomains"
            if settings.SECURE_HSTS_PRELOAD:
                hsts_val += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_val

        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        return response


# 2. Operational & Security Metrics Middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        metrics.record_http_request(request.method, response.status_code)
        if response.status_code >= 500:
            metrics.record_server_error()
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Correlation-ID"],
)


# 4. Secure Centralized Exception Handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Prevent detailed schema leakage in validation errors
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    client_ip = request.client.host if request.client else "unknown"

    # Emit structured security/application error event
    log_security_event(
        event_type="APPLICATION_ERROR",
        action="UNHANDLED_EXCEPTION",
        status_code=500,
        client_ip=client_ip,
        correlation_id=correlation_id,
        resource=str(request.url.path),
        details={"error_type": type(exc).__name__, "message": str(exc)},
        severity="ERROR",
    )
    metrics.record_server_error()

    # Generic error prevents database / internal stack trace exposure (CWE-209)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers={"X-Correlation-ID": correlation_id},
        content={
            "detail": "An internal server error occurred. Please contact the administrator.",
            "reference_id": correlation_id,
        },
    )


# 5. Register API Routers
app.include_router(health.router)
app.include_router(metrics_router.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(reports.router)

# 6. Register Web UI Router
app.include_router(web.router)
