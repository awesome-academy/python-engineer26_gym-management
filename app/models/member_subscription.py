from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MemberSubscription(Base):
    __tablename__ = "member_subscriptions"

    member_id: Mapped[str] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    package_id: Mapped[str] = mapped_column(
        ForeignKey("packages.id", ondelete="RESTRICT"), nullable=False
    )
    subscription_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    subscription_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
