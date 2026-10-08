from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.app.models.user import RevokedToken, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username.lower()).first()

    def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email.lower(), username=username.lower(), password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def is_token_revoked(self, jti: str) -> bool:
        return self.db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None

    def revoke_token(self, user_id: int, jti: str, expires_at: datetime) -> RevokedToken:
        revoked = RevokedToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self.db.add(revoked)
        self.db.commit()
        return revoked
