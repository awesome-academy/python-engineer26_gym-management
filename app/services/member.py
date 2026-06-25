from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories.member import MemberRepository
from app.schemas.common import PaginatedResponse
from app.schemas.member import (
    CreateMemberRequest,
    UpdateMemberRequest,
    MemberResponse,
    MemberListQuery,
)


class MemberService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = MemberRepository(session)

    async def create(self, payload: CreateMemberRequest) -> MemberResponse:
        existing_member = await self._repo.get_one({"phone": payload.phone})
        if existing_member:
            raise ConflictException(f"Phone number '{payload.phone}' already exists")

        try:
            member = await self._repo.create(
                phone=payload.phone,
                full_name=payload.full_name,
                date_of_birth=payload.date_of_birth,
                gender=payload.gender,
                avatar_url=payload.avatar_url,
                note=payload.note,
            )
            await self._repo.session.flush()
        except IntegrityError as e:
            await self._repo.session.rollback()
            raise ConflictException(
                f"Phone number '{payload.phone}' already exists"
            ) from e

        return MemberResponse.model_validate(member, from_attributes=True)

    async def get(self, member_id: str) -> MemberResponse:
        member = await self._repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id '{member_id}' not found")
        return MemberResponse.model_validate(member, from_attributes=True)

    async def update(
        self, member_id: str, payload: UpdateMemberRequest
    ) -> MemberResponse:
        member = await self._repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id '{member_id}' not found")

        if payload.phone and payload.phone != member.phone:
            existing_member = await self._repo.get_one({"phone": payload.phone})
            if existing_member:
                raise ConflictException(
                    f"Phone number '{payload.phone}' already exists"
                )

        update_data = payload.model_dump(exclude_unset=True)

        try:
            updated_member = await self._repo.update(member, **update_data)
            await self._repo.session.flush()
        except IntegrityError as e:
            await self._repo.session.rollback()
            raise ConflictException(
                f"Phone number '{payload.phone}' already exists"
            ) from e

        return MemberResponse.model_validate(updated_member, from_attributes=True)

    async def get_list(
        self,
        query: MemberListQuery,
    ) -> PaginatedResponse[MemberResponse]:
        members = await self._repo.paginate(
            page=query.page,
            limit=query.limit,
            phone__ilike=query.phone or None,
            full_name__ilike=query.full_name or None,
        )

        return PaginatedResponse[MemberResponse](
            items=[
                MemberResponse.model_validate(member, from_attributes=True)
                for member in members.items
            ],
            total=members.total,
            page=members.page,
            limit=members.limit,
        )

    async def delete(self, member_id: str) -> None:
        member = await self._repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id '{member_id}' not found")

        await self._repo.delete(member)
