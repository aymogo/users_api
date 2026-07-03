from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    """Encapsulates all direct DB access for the User model (Repository pattern)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[User]:
        stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self._session.delete(user)

    async def save(self, user: User) -> User:
        """Persist changes made to an already-tracked entity."""
        await self._session.flush()
        await self._session.refresh(user)
        return user