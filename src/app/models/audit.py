from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from src.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    client_ip = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=True)
    resource = Column(String(100), nullable=False)
    status_code = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)  # Masked JSON metadata

    __table_args__ = (
        Index("idx_audit_user_time", "user_id", "timestamp"),
        Index("idx_audit_event_time", "event_type", "timestamp"),
    )
