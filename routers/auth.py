from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from dependencies import get_db, templates
from services.authentication import AuthenticationError, authenticate_user

router = APIRouter(tags=["auth"])


@router.post("/login", name="login_post", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(default=""),
    password: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(db, email, password)
        request.session.clear()
        request.session["email"] = user.email
        request.session["user_name"] = user.name
        return RedirectResponse(url="/profile", status_code=303)
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "errors": exc.errors, "form": {"email": email}},
            status_code=422,
        )


@router.get("/logout", name="logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
