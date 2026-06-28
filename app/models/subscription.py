from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enum import SubscriptionStatus
from app.models.base import Base


class Subscription(Base):
    """Subscription model for gym member subscriptions"""

    __tablename__ = "subscriptions"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id"), nullable=False)
    package_id: Mapped[str] = mapped_column(ForeignKey("packages.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SubscriptionStatus.PENDING,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    sold_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
