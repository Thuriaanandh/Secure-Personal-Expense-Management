from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    category_id: int = Field(..., ge=1)
    amount: Decimal = Field(..., gt=Decimal("0.00"), le=Decimal("1000000.00"), decimal_places=2)
    type: str = Field(..., pattern=r"^(INCOME|EXPENSE)$")
    transaction_date: date
    description: Optional[str] = Field(None, max_length=255)

    model_config = {"extra": "forbid"}


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = Field(None, ge=1)
    amount: Optional[Decimal] = Field(
        None, gt=Decimal("0.00"), le=Decimal("1000000.00"), decimal_places=2
    )
    type: Optional[str] = Field(None, pattern=r"^(INCOME|EXPENSE)$")
    transaction_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=255)

    model_config = {"extra": "forbid"}


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    category_name: Optional[str] = None
    amount: Decimal
    type: str
    transaction_date: date
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionFilterParams(BaseModel):
    keyword: Optional[str] = Field(None, max_length=100, pattern=r"^[a-zA-Z0-9_\-\s]*$")
    category_id: Optional[int] = Field(None, ge=1)
    type: Optional[str] = Field(None, pattern=r"^(INCOME|EXPENSE)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    model_config = {"extra": "forbid"}


class MonthlySummaryResponse(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    category_breakdown: Dict[str, Decimal]
    transaction_count: int
