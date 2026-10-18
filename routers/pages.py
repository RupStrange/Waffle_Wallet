from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from dependencies import get_db, templates
from schemas.user import UserCreate
from services.registration import RegistrationError, register_user

router = APIRouter(tags=["pages"])


def registration_form(
    name: str = Form(default=""),
    email: str = Form(default=""),
    password: str = Form(default=""),
) -> UserCreate:
    return UserCreate(name=name, email=email, password=password)


@router.get("/", name="landing", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@router.get("/register", name="register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", name="register_post", response_class=HTMLResponse)
async def register_post(
    request: Request,
    user_in: Annotated[UserCreate, Depends(registration_form)],
    confirm_password: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        register_user(db, confirm_password=confirm_password, **user_in.model_dump())
        return RedirectResponse(url="/login", status_code=303)
    except RegistrationError as exc:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": exc.errors, "form": {"name": user_in.name, "email": user_in.email}},
            status_code=422,
        )


@router.get("/login", name="login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/terms", name="terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@router.get("/privacy", name="privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})
