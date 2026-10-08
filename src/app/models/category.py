from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)  # INCOME, EXPENSE, BOTH
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    owner = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_category_name"),)
