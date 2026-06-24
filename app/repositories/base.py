from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, inspect
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import RelationshipProperty, selectinload

from app.models import Base
from app.schemas import PaginatedResponse

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: str) -> ModelT | None:
        stmt = select(self.model).where(
            (self.model.id == item_id) & (self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_one(
        self,
        conditions: dict[str, Any] | None = None,
        load: list[str] | None = None,
    ) -> ModelT | None:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        if conditions:
            for attr, value in conditions.items():
                if value is None:
                    continue
                col = getattr(self.model, attr, None)
                if col is None:
                    raise ValueError(
                        f"Invalid filter field '{attr}' for {self.model.__name__}"
                    )
                stmt = stmt.where(col == value)

        if load:
            for relationship in load:
                rel = getattr(self.model, relationship, None)
                if rel is None:
                    raise ValueError(
                        f"Invalid relationship '{relationship}' for {self.model.__name__}"
                    )
                stmt = stmt.options(selectinload(rel))

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, **kwargs: Any) -> ModelT:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now()
            await self._cascade_soft_delete(instance)
            await self.session.flush()

    async def _cascade_soft_delete(self, instance: ModelT) -> None:
        mapper = inspect(type(instance))

        for rel in mapper.relationships:
            if isinstance(rel, RelationshipProperty):
                try:
                    related_attr = getattr(instance, rel.key, None)
                except InvalidRequestError:
                    continue

                if related_attr is None:
                    continue

                if isinstance(related_attr, list):
                    for related_obj in related_attr:
                        if hasattr(related_obj, "deleted_at"):
                            related_obj.deleted_at = datetime.now()
                            await self._cascade_soft_delete(related_obj)

    async def paginate(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
        load: list[str] | None = None,
        **filters: Any,
    ) -> PaginatedResponse:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        count_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.deleted_at.is_(None))
        )

        if load:
            for relationship in load:
                rel = getattr(self.model, relationship, None)
                if rel is None:
                    raise ValueError(
                        f"Invalid relationship '{relationship}' for {self.model.__name__}"
                    )
                stmt = stmt.options(selectinload(rel))

        for attr, value in filters.items():
            if value is None:
                continue

            field_name, operator = self._parse_filter(attr)
            col = getattr(self.model, field_name, None)
            if col is None:
                raise ValueError(
                    f"Invalid filter field '{field_name}' for {self.model.__name__}"
                )

            condition = self._build_filter_condition(col, operator, value)
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        sort_col = getattr(self.model, sort_by, None)
        if sort_col is None:
            raise ValueError(
                f"Invalid sort field '{sort_by}' for {self.model.__name__}"
            )

        if order.lower() == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        total = (await self.session.execute(count_stmt)).scalar_one()
        offset = (page - 1) * limit
        rows = (
            (await self.session.execute(stmt.offset(offset).limit(limit)))
            .scalars()
            .all()
        )

        return PaginatedResponse(items=list(rows), total=total, page=page, limit=limit)

    def _parse_filter(self, attr: str) -> tuple[str, str]:
        if "__" not in attr:
            return attr, "eq"

        field_name, operator = attr.rsplit("__", 1)
        return field_name, operator.lower()

    def _build_filter_condition(
        self,
        col: Any,
        operator: str,
        value: Any,
    ) -> ColumnElement[bool]:
        if operator == "eq":
            return col == value
        if operator == "like":
            return col.like(f"%{value}%")
        if operator == "ilike":
            return col.ilike(f"%{value}%")

        raise ValueError(f"Invalid filter operator '{operator}'")
