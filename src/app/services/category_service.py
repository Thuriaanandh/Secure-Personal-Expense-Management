from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from src.app.models.category import Category
from src.app.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)

    def get_accessible_categories(self, user_id: int) -> List[Category]:
        return self.category_repo.get_accessible_categories(user_id)

    def create_custom_category(
        self, user_id: int, name: str, cat_type: str
    ) -> Tuple[Optional[Category], Optional[str]]:
        # Check if already exists for this tenant
        existing = [
            c for c in self.get_accessible_categories(user_id) if c.name.lower() == name.lower()
        ]
        if existing:
            return None, "Category with this name already exists."

        category = self.category_repo.create_custom(user_id=user_id, name=name, cat_type=cat_type)
        return category, None
