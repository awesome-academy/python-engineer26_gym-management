from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.member import Member


class CheckIn(Base):
    __tablename__ = "checkins"

    member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("members.id"), nullable=False
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    member: Mapped[Member] = relationship(
        "Member", primaryjoin="CheckIn.member_id == Member.id", foreign_keys=[member_id]
    )
