import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.app.models.audit import AuditLog

SENSITIVE_KEYS = {
    "password",
    "confirm_password",
    "token",
    "access_token",
    "secret",
    "password_hash",
    "authorization",
}


def mask_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                masked[k] = "[REDACTED]"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        event_type: str,
        resource: str,
        status_code: int,
        client_ip: str,
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        masked_details = None
        if details:
            clean = mask_sensitive_data(details)
            masked_details = json.dumps(clean)

        entry = AuditLog(
            event_type=event_type,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent[:250] if user_agent else None,
            resource=resource[:100],
            status_code=status_code,
            details=masked_details,
        )
        self.db.add(entry)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
        return entry
