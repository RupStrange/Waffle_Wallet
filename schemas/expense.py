from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from models.expense import VALID_CATEGORIES

# Single source of truth is models.expense.VALID_CATEGORIES. Type checkers
# cannot evaluate a non-literal here; Pydantic resolves it fine at runtime.
CATEGORY_TYPE = Literal[VALID_CATEGORIES]  # type: ignore[valid-type]

SORT_TYPE = Literal["date-desc", "date-asc", "amt-desc", "amt-asc"]


class ExpenseBase(BaseModel):
    amount: Decimal
    category: CATEGORY_TYPE
    date: date
    description: str | None = None


class ExpenseCreate(ExpenseBase):
    user_id: int


class ExpenseFilters(BaseModel):
    """
    Query-string parameters for GET /api/expenses.

    FastAPI reads each field from the URL query string (because the route
    declares Annotated[ExpenseFilters, Query()]), validates it, and hands
    the route a ready-made object. Every filter defaults to None, which
    means "do not filter on this".
    """
    model_config = {"extra": "forbid"}

    category: CATEGORY_TYPE | None = None
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = Field(default=None, ge=0)
    max_amount: Decimal | None = Field(default=None, ge=0)
    sort: SORT_TYPE = "date-desc"
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_ranges(self) -> "ExpenseFilters":
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValueError("min_amount cannot exceed max_amount")

        return self


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    limit: int
    offset: int
