from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from src.app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from src.app.models.user import User
from src.app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(
        self, email: str, username: str, password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        if not validate_password_strength(password):
            return (
                None,
                "Password does not meet complexity requirements (min 10 chars, uppercase, lowercase, digit, symbol).",
            )

        if self.user_repo.get_by_email(email):
            return None, "Email address is already registered."

        if self.user_repo.get_by_username(username):
            return None, "Username is already taken."

        password_hash = get_password_hash(password)
        user = self.user_repo.create(email=email, username=username, password_hash=password_hash)
        return user, None

    def authenticate(
        self, email_or_username: str, password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        # Supports email or username login
        user = None
        if "@" in email_or_username:
            user = self.user_repo.get_by_email(email_or_username)
        else:
            user = self.user_repo.get_by_username(email_or_username)

        if not user:
            return None, "Invalid email/username or password."

        if not user.is_active:
            return None, "Account has been suspended."

        if not verify_password(password, user.password_hash):
            return None, "Invalid email/username or password."

        return user, None

    def create_token_for_user(self, user: User) -> Dict[str, Any]:
        return create_access_token(subject=user.id)

    def logout(self, user_id: int, token: str) -> bool:
        if not token or not isinstance(token, str):
            return False
        token = token.strip()
        payload = decode_access_token(token)
        if not payload:
            return False
        jti = payload.get("jti")
        exp_timestamp = payload.get("exp")
        if not jti or not exp_timestamp:
            return False

        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        self.user_repo.revoke_token(user_id=user_id, jti=jti, expires_at=expires_at)
        return True

    def get_current_user_from_token(self, token: str) -> Optional[User]:
        if not token or not isinstance(token, str):
            return None
        token = token.strip()
        payload = decode_access_token(token)
        if not payload:
            return None

        jti = payload.get("jti")
        if not jti or self.user_repo.is_token_revoked(jti):
            return None

        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        try:
            user_id = int(user_id_str)
        except ValueError:
            return None

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None

        return user
