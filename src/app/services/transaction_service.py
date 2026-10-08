from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.app.models.transaction import Transaction
from src.app.repositories.category_repository import CategoryRepository
from src.app.repositories.transaction_repository import TransactionRepository
from src.app.schemas.transaction import (
    TransactionCreate,
    TransactionFilterParams,
    TransactionUpdate,
)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.txn_repo = TransactionRepository(db)
        self.cat_repo = CategoryRepository(db)

    def create_transaction(
        self, user_id: int, data: TransactionCreate
    ) -> Tuple[Optional[Transaction], Optional[str]]:
        # Verify category exists and belongs to system or caller
        category = self.cat_repo.get_by_id(data.category_id, user_id=user_id)
        if not category:
            return None, "Invalid category selected or category does not exist."

        txn = self.txn_repo.create(user_id=user_id, data=data)
        return txn, None

    def get_transaction(self, txn_id: int, user_id: int) -> Optional[Transaction]:
        """Compound lookup: returns record only if owned by user_id."""
        return self.txn_repo.get_by_id_and_user(txn_id=txn_id, user_id=user_id)

    def update_transaction(
        self, txn_id: int, user_id: int, data: TransactionUpdate
    ) -> Tuple[Optional[Transaction], Optional[str]]:
        if data.category_id:
            category = self.cat_repo.get_by_id(data.category_id, user_id=user_id)
            if not category:
                return None, "Invalid category selected."

        txn = self.txn_repo.update(txn_id=txn_id, user_id=user_id, data=data)
        if not txn:
            return None, "Transaction not found."
        return txn, None

    def delete_transaction(self, txn_id: int, user_id: int) -> bool:
        """Deletes record only if owned by user_id."""
        return self.txn_repo.delete(txn_id=txn_id, user_id=user_id)

    def list_transactions(
        self, user_id: int, filters: Optional[TransactionFilterParams] = None
    ) -> Tuple[List[Transaction], int]:
        return self.txn_repo.list_user_transactions(user_id=user_id, filters=filters)

    def get_monthly_summary(self, user_id: int, year: int, month: int) -> Dict:
        return self.txn_repo.get_monthly_summary(user_id=user_id, year=year, month=month)
