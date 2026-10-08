from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.core.dependencies import get_category_service, get_current_active_user
from src.app.models.user import User
from src.app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from src.app.services.category_service import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    current_user: User = Depends(get_current_active_user),
    service: CategoryService = Depends(get_category_service),
):
    return service.get_accessible_categories(user_id=current_user.id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_custom_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    service: CategoryService = Depends(get_category_service),
):
    category, error = service.create_custom_category(
        user_id=current_user.id, name=data.name, cat_type=data.type
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    service: CategoryService = Depends(get_category_service),
):
    category, error, status_code = service.update_custom_category(
        user_id=current_user.id,
        category_id=category_id,
        name=data.name,
        cat_type=data.type,
    )
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    service: CategoryService = Depends(get_category_service),
):
    success, error, status_code = service.delete_custom_category(
        user_id=current_user.id,
        category_id=category_id,
    )
    if error or not success:
        raise HTTPException(status_code=status_code, detail=error)
    return {"detail": "Category deleted successfully."}
