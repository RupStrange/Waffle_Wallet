"""
JSON API for querying a user's expenses — Step 5.

Unlike routers/expenses.py (HTML stubs for add/edit/delete), every route
here returns JSON and is scoped to the logged-in user via get_current_user.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import crud.expenses as crud_expenses
from dependencies import get_current_user, get_db
from models.user import User
from schemas.expense import ExpenseFilters, ExpenseListResponse

router = APIRouter(prefix="/api/expenses", tags=["api-expenses"])


@router.get(
    "",
    name="api_list_expenses",
    response_model=ExpenseListResponse,
    summary="List and filter the current user's expenses",
)
async def api_list_expenses(
    filters: Annotated[ExpenseFilters, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseListResponse:
    rows, total = crud_expenses.list_expenses(db, current_user.id, filters)
    return ExpenseListResponse(
        items=rows,
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )
