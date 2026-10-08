from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from src.app.models.category import Category
from src.app.models.transaction import Transaction
from src.app.schemas.transaction import (
    TransactionCreate,
    TransactionFilterParams,
    TransactionUpdate,
)


class TransactionRepository:
    """
    CRITICAL SSDLC TENANCY ENFORCEMENT:
    Every method requires `user_id: int` as an obligatory parameter.
    No query targets transactions by primary key alone.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id_and_user(self, txn_id: int, user_id: int) -> Optional[Transaction]:
        """Compound query enforcing tenant isolation (WHERE id = :id AND user_id = :uid)."""
        return (
            self.db.query(Transaction)
            .filter(Transaction.id == txn_id, Transaction.user_id == user_id)
            .first()
        )

    def list_user_transactions(
        self, user_id: int, filters: Optional[TransactionFilterParams] = None
    ) -> Tuple[List[Transaction], int]:
        """User-scoped query with parameterized filter bindings."""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if filters:
            if filters.category_id:
                query = query.filter(Transaction.category_id == filters.category_id)
            if filters.type:
                query = query.filter(Transaction.type == filters.type)
            if filters.start_date:
                query = query.filter(Transaction.transaction_date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.transaction_date <= filters.end_date)
            if filters.keyword:
                # Parameterized ILIKE clause prevents SQL injection (SEC-009)
                query = query.filter(Transaction.description.ilike(f"%{filters.keyword}%"))

        total_count = query.count()

        skip = filters.skip if filters else 0
        limit = filters.limit if filters else 50
        results = (
            query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return results, total_count

    def create(self, user_id: int, data: TransactionCreate) -> Transaction:
        """Binds caller user_id server-side. Client has no control over tenant assignment."""
        txn = Transaction(
            user_id=user_id,
            category_id=data.category_id,
            amount=data.amount,
            type=data.type,
            transaction_date=data.transaction_date,
            description=data.description,
        )
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def update(self, txn_id: int, user_id: int, data: TransactionUpdate) -> Optional[Transaction]:
        """Compound update ensuring row belongs to caller."""
        txn = self.get_by_id_and_user(txn_id=txn_id, user_id=user_id)
        if not txn:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(txn, key, value)

        self.db.commit()
        self.db.refresh(txn)
        return txn

    def delete(self, txn_id: int, user_id: int) -> bool:
        """Compound delete ensuring row belongs to caller."""
        txn = self.get_by_id_and_user(txn_id=txn_id, user_id=user_id)
        if not txn:
            return False

        self.db.delete(txn)
        self.db.commit()
        return True

    def get_monthly_summary(self, user_id: int, year: int, month: int) -> Dict:
        """Calculates tenant-scoped monthly aggregations using fixed-point arithmetic."""
        base_query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )

        income_sum = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.type == "INCOME",
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        ).scalar() or Decimal("0.00")

        expense_sum = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.type == "EXPENSE",
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        ).scalar() or Decimal("0.00")

        # Category breakdown for expenses
        cat_breakdown = (
            self.db.query(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "EXPENSE",
                extract("year", Transaction.transaction_date) == year,
                extract("month", Transaction.transaction_date) == month,
            )
            .group_by(Category.name)
            .all()
        )

        breakdown_dict = {cat_name: Decimal(str(cat_amt)) for cat_name, cat_amt in cat_breakdown}

        return {
            "year": year,
            "month": month,
            "total_income": Decimal(str(income_sum)),
            "total_expenses": Decimal(str(expense_sum)),
            "net_savings": Decimal(str(income_sum)) - Decimal(str(expense_sum)),
            "category_breakdown": breakdown_dict,
            "transaction_count": base_query.count(),
        }
