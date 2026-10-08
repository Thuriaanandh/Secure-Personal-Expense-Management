import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.app.core.config import get_settings

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{10,}$"
)


def validate_password_strength(password: str) -> bool:
    """Enforces NIST SP 800-63B aligned policy (SEC-002): >=10 chars, upper, lower, digit, symbol."""
    if not password or len(password) < 10:
        return False
    return bool(PASSWORD_REGEX.match(password))


def get_password_hash(password: str) -> str:
    """Hashes password using Argon2id with unique salt (SEC-001)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hash with constant-time comparison."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(subject: int, expires_delta: Optional[timedelta] = None) -> Dict[str, Any]:
    """Issues HMAC-SHA256 signed JWT with sub claim, exp, and unique jti (SEC-004)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": jti,
        "iss": "SPEMA-Auth",
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",  # nosec B105
        "expires_in": int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "jti": jti,
    }


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates token signature and claims."""
    if not token or not isinstance(token, str):
        return None
    token = token.strip()
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], issuer="SPEMA-Auth"
        )
        return payload
    except JWTError:
        return None
