from sqlalchemy.orm import Session

from database.db import pwd_context
from crud.users import get_user_by_email
from models.user import User


class AuthenticationError(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__(str(errors))


def authenticate_user(db: Session, email: str, password: str) -> User:
    errors: dict[str, str] = {}

    if not email.strip():
        errors["email"] = "Email address is required."
    if not password:
        errors["password"] = "Password is required."
    if errors:
        raise AuthenticationError(errors)

    user = get_user_by_email(db, email.strip())
    if not user or not pwd_context.verify(password, user.password_hash):
        raise AuthenticationError({"general": "Incorrect email or password."})

    return user
