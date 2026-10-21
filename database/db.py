from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import engine, Base, SessionLocal
import models  # registers User and Expense with Base.metadata

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db() -> None:
    """Create all tables directly from the models, bypassing Alembic.

    NOT called at startup any more -- Alembic owns the schema. Kept only for
    building a scratch/test database from scratch. Never run this against the
    real database: create_all() adds missing TABLES only, so a DB built this way
    silently diverges from one built by `alembic upgrade head` the moment a
    migration adds a column or index.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("[init_db] Tables created / verified.")
    except Exception as exc:
        print(f"[init_db] FAILED: {exc}")
        raise


def seed_db() -> None:
    """Insert demo user + 8 sample expenses. No-op if demo user already exists."""
    from models.user import User
    from models.expense import Expense

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "demo@wafflewallet.com").first()
        if existing:
            print("[seed_db] Demo user already present — skipping.")
            return

        today = date.today()
        demo_user = User(
            name="Demo User",
            email="demo@wafflewallet.com",
            password_hash=pwd_context.hash("demo123"),
        )
        db.add(demo_user)
        db.flush()  # populate demo_user.id before creating expenses

        expenses = [
            Expense(user_id=demo_user.id, amount=Decimal("45.50"),
                    category="Food", date=today - timedelta(days=1),
                    description="Grocery run"),
            Expense(user_id=demo_user.id, amount=Decimal("12.00"),
                    category="Transport", date=today - timedelta(days=2),
                    description="Bus pass"),
            Expense(user_id=demo_user.id, amount=Decimal("120.00"),
                    category="Bills", date=today - timedelta(days=5),
                    description="Electricity"),
            Expense(user_id=demo_user.id, amount=Decimal("30.00"),
                    category="Health", date=today - timedelta(days=7),
                    description="Pharmacy"),
            Expense(user_id=demo_user.id, amount=Decimal("18.99"),
                    category="Entertainment", date=today - timedelta(days=9),
                    description="Streaming subscription"),
            Expense(user_id=demo_user.id, amount=Decimal("65.00"),
                    category="Shopping", date=today - timedelta(days=12),
                    description="Clothing"),
            Expense(user_id=demo_user.id, amount=Decimal("9.50"),
                    category="Other", date=today - timedelta(days=14),
                    description="Miscellaneous"),
            Expense(user_id=demo_user.id, amount=Decimal("22.75"),
                    category="Food", date=today - timedelta(days=16),
                    description="Restaurant lunch"),
        ]
        db.add_all(expenses)
        db.commit()
        print("[seed_db] Demo user and 8 expenses created.")
    except Exception as exc:
        db.rollback()
        print(f"[seed_db] FAILED — rolled back: {exc}")
        raise
    finally:
        db.close()
