"""
Authenticated app pages — Step 4.

All three pages are currently static: every figure is a hardcoded
placeholder. A later step adds the analytics aggregates and an auth guard.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dependencies import templates

router = APIRouter(tags=["profile"])


@router.get("/profile", name="profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@router.get("/account", name="account", response_class=HTMLResponse)
async def account(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})


@router.get("/preferences", name="preferences", response_class=HTMLResponse)
async def preferences(request: Request):
    return templates.TemplateResponse("preferences.html", {"request": request})
