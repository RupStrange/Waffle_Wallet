"""
Reusable FastAPI dependencies and shared instances.

The `templates` instance is a singleton shared by all routers.
`main.py` patches `templates.env.globals["url_for"]` after the app and
its routes are registered, so any template rendered during a request will
see the fully-initialised url_for helper — no circular import required.
"""
from typing import Generator

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import SessionLocal

templates = Jinja2Templates(directory="templates")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
