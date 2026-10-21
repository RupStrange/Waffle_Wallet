"""
Shared pytest fixtures.

Key ideas
─────────
• SQLite in-memory DB per test — fast, zero setup, no shared state.
• `import models` at module level registers both tables on Base.metadata
  before create_all() runs. Skip it and every test fails with "no such table".
• TestClient(app) WITHOUT `with` — the context manager fires the lifespan,
  which runs seed_db() against the real PostgreSQL. Never do that.
• Dependency overrides swap get_db and get_current_user without touching
  the real session, cookie or database.
• Always clear dependency_overrides in teardown — it is global mutable
  state on `app` and leaks into other test files if left set.
"""
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 — registers User and Expense on Base.metadata
from database import Base
from dependencies import get_current_user, get_db
from main import app
from models.expense import Expense
from models.user import User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seed_users(db_session):
    user_a = User(name="Alice", email="alice@test.com", password_hash="x")
    user_b = User(name="Bob",   email="bob@test.com",   password_hash="x")
    db_session.add_all([user_a, user_b])
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)
    return user_a, user_b


@pytest.fixture
def make_expense(db_session):
    """Factory: call it to insert one expense row and get the ORM object back."""
    def _make(
        user_id: int,
        amount: str = "25.00",
        category: str = "Food",
        expense_date: date = date(2026, 1, 15),
        description: str | None = None,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            amount=Decimal(amount),
            category=category,
            date=expense_date,
            description=description,
        )
        db_session.add(expense)
        db_session.commit()
        db_session.refresh(expense)
        return expense
    return _make


@pytest.fixture
def client(db_session, seed_users):
    user_a, _ = seed_users
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user_a
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_as_b(db_session, seed_users):
    _, user_b = seed_users
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user_b
    yield TestClient(app)
    app.dependency_overrides.clear()
