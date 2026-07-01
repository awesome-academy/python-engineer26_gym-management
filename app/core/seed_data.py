from __future__ import annotations

import asyncio
import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select, text

from app.core.database import AsyncSessionFactory
from app.core.enum import SubscriptionStatus, UserRole
from app.core.security import hash_password
from app.models.checkin import CheckIn
from app.models.member import Member
from app.models.package import Package
from app.models.subscription import Subscription
from app.models.user import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DEFAULT_USER_COUNT = 20
DEFAULT_MEMBER_COUNT = 300
DEFAULT_SUBSCRIPTION_COUNT = 300
DEFAULT_CHECKIN_COUNT = 600
RESET_EXISTING = os.getenv("SEED_RESET", "0").lower() in {"1", "true", "yes"}


async def _reset_existing_data(session: Any) -> None:
    if not RESET_EXISTING:
        return

    logger.info("Resetting existing seed data...")
    await session.execute(delete(CheckIn))
    await session.execute(delete(Subscription))
    await session.execute(delete(Member))
    await session.execute(delete(Package))
    await session.execute(delete(User))
    await session.commit()


async def seed_database() -> None:
    async with AsyncSessionFactory() as session:
        try:
            await _reset_existing_data(session)

            logger.info("Creating users...")
            admin = await session.scalar(select(User).where(User.username == "admin"))
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    full_name="Admin User",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                session.add(admin)
                await session.flush()

            staff = await session.scalar(select(User).where(User.username == "staff"))
            if not staff:
                staff = User(
                    username="staff",
                    password_hash=hash_password("staff123"),
                    full_name="Staff User",
                    role=UserRole.STAFF,
                    is_active=True,
                )
                session.add(staff)
                await session.flush()

            for idx in range(1, DEFAULT_USER_COUNT + 1):
                username = f"staff_{idx}"
                existing_user = await session.scalar(
                    select(User).where(User.username == username)
                )
                if existing_user:
                    continue
                user = User(
                    username=username,
                    password_hash=hash_password(f"pass{idx:03d}"),
                    full_name=f"Staff User {idx}",
                    role=UserRole.STAFF,
                    is_active=True,
                )
                session.add(user)
                await session.flush()

            logger.info("Creating packages...")
            package_templates = [
                (
                    "Basic 1 Month",
                    "Unlimited access for one month",
                    30,
                    Decimal("300000"),
                ),
                (
                    "Premium 3 Months",
                    "Unlimited access for three months",
                    90,
                    Decimal("800000"),
                ),
                (
                    "Annual Pass",
                    "Unlimited access for one year",
                    365,
                    Decimal("2500000"),
                ),
                ("10 Session Pass", "Ten training sessions", 60, Decimal("500000")),
                ("VIP Pass", "VIP access with extra perks", 120, Decimal("1500000")),
                ("Weekend Pass", "Access on weekends only", 45, Decimal("450000")),
            ]
            packages: list[Package] = []
            for name, description, duration_days, price in package_templates:
                existing_package = await session.scalar(
                    select(Package).where(Package.name == name)
                )
                if existing_package:
                    packages.append(existing_package)
                    continue
                package = Package(
                    name=name,
                    description=description,
                    duration_days=duration_days,
                    price=price,
                    is_active=True,
                )
                session.add(package)
                await session.flush()
                packages.append(package)

            logger.info("Creating members...")
            members: list[Member] = []
            for idx in range(1, DEFAULT_MEMBER_COUNT + 1):
                phone = f"090{idx:08d}"
                existing_member = await session.scalar(
                    select(Member).where(Member.phone == phone)
                )
                if existing_member:
                    members.append(existing_member)
                    continue
                member = Member(
                    phone=phone,
                    full_name=f"Member {idx}",
                    date_of_birth=date(
                        1985 + (idx % 20), 1 + (idx % 12), 1 + (idx % 28)
                    ),
                    gender="male" if idx % 2 == 0 else "female",
                    note=f"Seeded member #{idx}",
                )
                session.add(member)
                await session.flush()
                members.append(member)

            logger.info("Creating subscriptions...")
            subscription_count = min(DEFAULT_SUBSCRIPTION_COUNT, len(members))
            member_ids_for_checkins: list[str] = []
            for idx in range(subscription_count):
                member = members[idx]
                package = packages[idx % len(packages)]
                start_date = date.today() - timedelta(days=30 + (idx % 60))
                end_date = start_date + timedelta(days=package.duration_days)
                status = (
                    SubscriptionStatus.ACTIVE
                    if idx % 3 == 0
                    else SubscriptionStatus.PENDING
                    if idx % 3 == 1
                    else SubscriptionStatus.EXPIRED
                    if idx % 4 == 2
                    else SubscriptionStatus.CANCELLED
                )
                existing_result = await session.execute(
                    text(
                        """
                        SELECT 1
                        FROM subscriptions
                        WHERE member_id = :member_id AND package_id = :package_id
                        LIMIT 1
                        """
                    ),
                    {"member_id": member.id, "package_id": package.id},
                )
                existing = existing_result.scalar_one_or_none()
                if existing:
                    member_ids_for_checkins.append(member.id)
                    continue

                insert_stmt = text(
                    """
                    INSERT INTO subscriptions (
                        id, member_id, package_id, start_date, end_date, status, price, created_by
                    ) VALUES (
                        :id, :member_id, :package_id, :start_date, :end_date, :status, :price, :created_by
                    )
                    """
                )
                await session.execute(
                    insert_stmt,
                    {
                        "id": str(uuid4()),
                        "member_id": member.id,
                        "package_id": package.id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "status": status.value,
                        "price": str(package.price),
                        "created_by": admin.id,
                    },
                )
                member_ids_for_checkins.append(member.id)

            logger.info("Creating check-ins...")
            if not member_ids_for_checkins:
                raise RuntimeError("No members were seeded; cannot create check-ins")

            for idx in range(
                min(DEFAULT_CHECKIN_COUNT, len(member_ids_for_checkins) * 3)
            ):
                member_id = member_ids_for_checkins[idx % len(member_ids_for_checkins)]
                checked_in_at = datetime.now(timezone.utc) - timedelta(
                    days=idx // 6,
                    hours=(idx % 24),
                    minutes=(idx % 60),
                )
                checkin = CheckIn(
                    member_id=member_id,
                    checked_in_at=checked_in_at,
                    note=f"Auto-generated check-in #{idx + 1}",
                )
                session.add(checkin)

            await session.commit()
            logger.info(
                "Seed completed successfully with %s users, %s members, %s subscriptions, and %s check-ins",
                DEFAULT_USER_COUNT + 2,
                len(members),
                subscription_count,
                min(DEFAULT_CHECKIN_COUNT, len(member_ids_for_checkins) * 3),
            )
        except Exception as exc:
            await session.rollback()
            logger.error("Failed to seed database: %s", exc, exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
