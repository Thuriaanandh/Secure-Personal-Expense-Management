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

    def update_custom_category(
        self, user_id: int, category_id: int, name: Optional[str], cat_type: Optional[str]
    ) -> Tuple[Optional[Category], Optional[str], int]:
        cat = self.category_repo.db.query(Category).filter(Category.id == category_id).first()
        if not cat:
            return None, "Category not found.", 404
        if cat.is_system:
            return None, "System categories cannot be modified.", 403
        if cat.user_id != user_id:
            return None, "Category not found.", 404

        if name:
            existing = [
                c
                for c in self.get_accessible_categories(user_id)
                if c.name.lower() == name.lower() and c.id != category_id
            ]
            if existing:
                return None, "Category with this name already exists.", 400

        updated = self.category_repo.update_custom(category=cat, name=name, cat_type=cat_type)
        return updated, None, 200

    def delete_custom_category(
        self, user_id: int, category_id: int
    ) -> Tuple[bool, Optional[str], int]:
        cat = self.category_repo.db.query(Category).filter(Category.id == category_id).first()
        if not cat:
            return False, "Category not found.", 404
        if cat.is_system:
            return False, "System categories cannot be deleted.", 403
        if cat.user_id != user_id:
            return False, "Category not found.", 404

        success, err = self.category_repo.delete_custom(category=cat)
        if not success:
            return False, err, 400
        return True, None, 200
