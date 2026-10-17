"""
Expense routes — placeholder implementations preserved from the Flask original.
Students will implement these in Steps 7–9.
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/add", name="add_expense", response_class=PlainTextResponse)
async def add_expense():
    return "Add expense — coming in Step 7"


@router.get("/{id}/edit", name="edit_expense", response_class=PlainTextResponse)
async def edit_expense(id: int):
    return "Edit expense — coming in Step 8"


@router.get("/{id}/delete", name="delete_expense", response_class=PlainTextResponse)
async def delete_expense(id: int):
    return "Delete expense — coming in Step 9"
