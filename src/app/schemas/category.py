from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_\-\s]+$")
    type: str = Field(default="EXPENSE", pattern=r"^(INCOME|EXPENSE|BOTH)$")

    model_config = {"extra": "forbid"}


class CategoryResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    type: str
    is_system: bool
    created_at: datetime

    model_config = {"from_attributes": True}
