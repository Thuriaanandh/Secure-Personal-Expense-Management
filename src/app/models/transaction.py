from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from src.app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # MANDATORY OWNER: Enforces primary security rule (NOT NULL)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # INCOME, EXPENSE
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount > 0.00", name="chk_positive_amount"),
        CheckConstraint("type IN ('INCOME', 'EXPENSE')", name="chk_transaction_type"),
        Index("idx_txn_user_date", "user_id", "transaction_date"),
        Index("idx_txn_user_type", "user_id", "type"),
        Index("idx_txn_user_cat", "user_id", "category_id"),
    )
