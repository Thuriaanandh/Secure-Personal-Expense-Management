from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def log(
        self,
        event_type: str,
        resource: str,
        status_code: int,
        client_ip: str,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        return self.audit_repo.log_event(
            event_type=event_type,
            resource=resource,
            status_code=status_code,
            client_ip=client_ip,
            user_id=user_id,
            user_agent=user_agent,
            details=details,
        )
