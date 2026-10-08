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
from src.app.routers import auth, categories, health, reports, transactions, web

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
    yield
    # Shutdown
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


# 1. Security Headers Middleware (OWASP Secure Headers Project)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
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


app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# 3. Secure Centralized Exception Handling
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
    correlation_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception [ref:{correlation_id}]: {str(exc)}", exc_info=True)
    # Generic error prevents database / internal stack trace exposure (CWE-209)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact the administrator.",
            "reference_id": correlation_id,
        },
    )


# 4. Register API Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(reports.router)

# 5. Register Web UI Router
app.include_router(web.router)
