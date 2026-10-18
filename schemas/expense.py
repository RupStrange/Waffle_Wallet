from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel

CATEGORY_TYPE = Literal[
    "Food", "Transport", "Bills", "Health",
    "Entertainment", "Shopping", "Other"
]


class ExpenseBase(BaseModel):
    amount: Decimal
    category: CATEGORY_TYPE
    date: date
    description: str | None = None


class ExpenseCreate(ExpenseBase):
    user_id: int


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
