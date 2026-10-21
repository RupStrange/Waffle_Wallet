from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Integer, Numeric, String, Text, Date, DateTime, ForeignKey, CheckConstraint, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

VALID_CATEGORIES = ("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other")

# SQL literal list derived from VALID_CATEGORIES, e.g. "'Food','Transport',..."
# Keeps the CHECK constraint in lockstep with the tuple above.
_CATEGORY_SQL_LIST = ",".join(f"'{c}'" for c in VALID_CATEGORIES)


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        CheckConstraint(
            f"category IN ({_CATEGORY_SQL_LIST})",
            name="ck_expenses_category_valid",
        ),
        Index("ix_expenses_user_id_date", "user_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="expenses")
