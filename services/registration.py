from sqlalchemy.orm import Session

from database.db import pwd_context
from crud.users import get_user_by_email, create_user
from models.user import User


class RegistrationError(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__(str(errors))


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    confirm_password: str,
) -> User:
    errors: dict[str, str] = {}

    if not name.strip():
        errors["name"] = "Full name is required."
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    elif password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    if errors:
        raise RegistrationError(errors)

    if get_user_by_email(db, email):
        raise RegistrationError({"email": "An account with that email already exists."})

    password_hash = pwd_context.hash(password)
    return create_user(db, name=name.strip(), email=email, password_hash=password_hash)
