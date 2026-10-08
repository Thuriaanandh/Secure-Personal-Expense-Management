from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.models.user import User
from src.app.services.audit_service import AuditService
from src.app.services.auth_service import AuthService
from src.app.services.category_service import CategoryService
from src.app.services.reporting_service import ReportingService
from src.app.services.transaction_service import TransactionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(db)


def get_reporting_service(db: Session = Depends(get_db)) -> ReportingService:
    return ReportingService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)


def get_current_active_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    CENTRALIZED AUTHORIZATION GATE:
    Extracts Bearer token from header or cookie; verifies signature, claims, and revocation.
    Derives user identity exclusively server-side.
    """
    # Fallback if oauth2_scheme did not resolve token from non-standard header formats
    if not token:
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header:
            parts = auth_header.split(maxsplit=1)
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1].strip()
            elif len(parts) == 1 and not parts[0].lower().startswith("bearer"):
                token = parts[0].strip()

    # Fallback to cookie if authorization header is omitted (for web UI navigation)
    if not token and "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Robust sanitization: strip any leading or trailing whitespace
    token = token.strip()

    user = auth_service.get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
