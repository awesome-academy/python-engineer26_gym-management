from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Member
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    model = Member

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
