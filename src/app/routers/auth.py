import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.app.core.config import get_settings
from src.app.core.dependencies import (
    get_audit_service,
    get_auth_service,
    get_current_active_user,
)
from src.app.models.user import User
from src.app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from src.app.services.audit_service import AuditService
from src.app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# In-memory sliding window rate limiter for failed login attempts
LOGIN_ATTEMPTS: Dict[str, list] = {}


def check_rate_limit(key: str, max_attempts: int, window_seconds: int):
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(key, [])
    # Filter attempts within active sliding window
    valid_attempts = [t for t in attempts if now - t < window_seconds]
    LOGIN_ATTEMPTS[key] = valid_attempts
    if len(valid_attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please retry later.",
        )


def record_failed_attempt(key: str):
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(key, [])
    attempts.append(now)
    LOGIN_ATTEMPTS[key] = attempts


def reset_rate_limit(key: str):
    LOGIN_ATTEMPTS.pop(key, None)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"reg_{client_ip}", max_attempts=10, window_seconds=900)
    record_failed_attempt(f"reg_{client_ip}")

    user, error = auth_service.register(
        email=data.email, username=data.username, password=data.password
    )
    if error:
        audit_service.log(
            event_type="REGISTER_FAILED",
            resource="/api/v1/auth/register",
            status_code=400,
            client_ip=client_ip,
            details={"reason": error, "email": data.email},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    audit_service.log(
        event_type="REGISTER_SUCCESS",
        resource="/api/v1/auth/register",
        status_code=201,
        client_ip=client_ip,
        user_id=user.id,
        details={"username": user.username},
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"login_{client_ip}_{data.email_or_username.lower()}"

    check_rate_limit(
        rate_limit_key,
        max_attempts=settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )

    user, error = auth_service.authenticate(
        email_or_username=data.email_or_username, password=data.password
    )
    if error:
        record_failed_attempt(rate_limit_key)
        audit_service.log(
            event_type="AUTH_FAILURE",
            resource="/api/v1/auth/login",
            status_code=401,
            client_ip=client_ip,
            details={"reason": error, "identifier": data.email_or_username},
        )
        # Uniform 401 prevents username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authentication succeeded: reset failure counter to avoid locking out legitimate users
    reset_rate_limit(rate_limit_key)

    token_dict = auth_service.create_token_for_user(user)

    # Set secure HttpOnly cookie for web UI sessions
    response.set_cookie(
        key="access_token",
        value=token_dict["access_token"],
        max_age=token_dict["expires_in"],
        httponly=True,
        samesite="lax",
        secure=False,  # Allow localhost in dev/testing; True in production
    )

    audit_service.log(
        event_type="AUTH_SUCCESS",
        resource="/api/v1/auth/login",
        status_code=200,
        client_ip=client_ip,
        user_id=user.id,
    )
    return token_dict


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if token:
        auth_service.logout(user_id=current_user.id, token=token)

    response.delete_cookie(key="access_token")
    client_ip = request.client.host if request.client else "unknown"
    audit_service.log(
        event_type="LOGOUT",
        resource="/api/v1/auth/logout",
        status_code=200,
        client_ip=client_ip,
        user_id=current_user.id,
    )
    return {"detail": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
