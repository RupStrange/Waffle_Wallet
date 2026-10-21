
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.expense import Expense
from schemas.expense import ExpenseFilters


SORT_OPTIONS = {
    "date-desc": (Expense.date.desc(),   Expense.id.desc()),
    "date-asc":  (Expense.date.asc(),    Expense.id.asc()),
    "amt-desc":  (Expense.amount.desc(), Expense.id.desc()),
    "amt-asc":   (Expense.amount.asc(),  Expense.id.asc()),
}


def list_expenses(
    db: Session,
    user_id: int,
    filters: ExpenseFilters,
) -> tuple[Sequence[Expense], int]:
    """
    Return (page_of_rows, total_matching_rows).

    `user_id` is a separate REQUIRED argument, deliberately NOT a field of
    `filters`: it comes from the session, never from the request.
    """
    # 1. Base condition — always applied, non-negotiable
    conditions = [Expense.user_id == user_id]

    # 2. Append one condition per supplied filter
    if filters.category is not None:
        conditions.append(Expense.category == filters.category)
    if filters.start_date is not None:
        conditions.append(Expense.date >= filters.start_date)
    if filters.end_date is not None:
        conditions.append(Expense.date <= filters.end_date)
    if filters.min_amount is not None:
        conditions.append(Expense.amount >= filters.min_amount)
    if filters.max_amount is not None:
        conditions.append(Expense.amount <= filters.max_amount)

    # 3. One filtered statement reused for both queries
    stmt = select(Expense).where(*conditions)

    # 4. Count — same WHERE conditions, but just count the ids
    count = db.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0

    # 5. Page — add ORDER BY + LIMIT + OFFSET on top of the filtered rows
    sort_columns = SORT_OPTIONS[filters.sort]
    page_stmt = stmt.order_by(*sort_columns).limit(filters.limit).offset(filters.offset)
    rows = db.scalars(page_stmt).all()

    return rows, count