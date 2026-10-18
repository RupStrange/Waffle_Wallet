from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalars(stmt).first()


def create_user(db: Session, name: str, email: str, password_hash: str) -> User:
    user = User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
