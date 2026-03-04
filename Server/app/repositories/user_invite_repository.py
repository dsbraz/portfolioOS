import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user_invite import UserInvite


class UserInviteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, invite: UserInvite) -> UserInvite:
        self._session.add(invite)
        await self._session.flush()
        await self._session.refresh(invite)
        return invite

    async def update(self, invite: UserInvite) -> UserInvite:
        await self._session.flush()
        await self._session.refresh(invite)
        return invite

    async def get_by_token(self, token: uuid.UUID) -> UserInvite | None:
        result = await self._session.execute(
            select(UserInvite).where(UserInvite.token == token)
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(
        self, email: str, now: datetime
    ) -> UserInvite | None:
        result = await self._session.execute(
            select(UserInvite).where(
                UserInvite.email == email,
                UserInvite.used_at.is_(None),
                UserInvite.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, invite: UserInvite, now: datetime) -> UserInvite:
        invite.expires_at = now
        return await self.update(invite)

    async def mark_used(self, invite: UserInvite, now: datetime) -> UserInvite:
        invite.used_at = now
        return await self.update(invite)

    async def get_all_active(
        self, now: datetime
    ) -> tuple[list[UserInvite], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(UserInvite)
            .where(
                UserInvite.used_at.is_(None),
                UserInvite.expires_at > now,
            )
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(UserInvite)
            .where(
                UserInvite.used_at.is_(None),
                UserInvite.expires_at > now,
            )
            .order_by(UserInvite.created_at.desc())
        )
        return list(result.scalars().all()), total
