from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.app.models.category import Category

DEFAULT_SYSTEM_CATEGORIES = [
    ("Salary", "INCOME"),
    ("Freelance / Consulting", "INCOME"),
    ("Investment Returns", "INCOME"),
    ("Housing & Rent", "EXPENSE"),
    ("Groceries & Food", "EXPENSE"),
    ("Utilities & Bills", "EXPENSE"),
    ("Transportation", "EXPENSE"),
    ("Healthcare", "EXPENSE"),
    ("Entertainment & Leisure", "EXPENSE"),
]


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
        self._ensure_system_categories()

    def _ensure_system_categories(self):
        # Seed system categories if absent
        count = self.db.query(Category).filter(Category.is_system.is_(True)).count()
        if count == 0:
            for name, cat_type in DEFAULT_SYSTEM_CATEGORIES:
                cat = Category(user_id=None, name=name, type=cat_type, is_system=True)
                self.db.add(cat)
            self.db.commit()

    def get_accessible_categories(self, user_id: int) -> List[Category]:
        # Returns system categories + custom categories owned by user_id
        return (
            self.db.query(Category)
            .filter(or_(Category.is_system.is_(True), Category.user_id == user_id))
            .order_by(Category.name.asc())
            .all()
        )

    def get_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        # Verifies category exists and is accessible by this tenant
        return (
            self.db.query(Category)
            .filter(
                Category.id == category_id,
                or_(Category.is_system.is_(True), Category.user_id == user_id),
            )
            .first()
        )

    def create_custom(self, user_id: int, name: str, cat_type: str) -> Category:
        category = Category(user_id=user_id, name=name, type=cat_type, is_system=False)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_custom(
        self, category: Category, name: Optional[str], cat_type: Optional[str]
    ) -> Category:
        if name is not None:
            category.name = name
        if cat_type is not None:
            category.type = cat_type
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_custom(self, category: Category) -> Tuple[bool, Optional[str]]:
        from src.app.models.transaction import Transaction

        txn_count = (
            self.db.query(Transaction).filter(Transaction.category_id == category.id).count()
        )
        if txn_count > 0:
            return (
                False,
                "Cannot delete category with associated transactions. Reassign or delete transactions first.",
            )
        self.db.delete(category)
        self.db.commit()
        return True, None
