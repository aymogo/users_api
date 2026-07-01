from core.exceptions import UserNotFoundError
from models.user import User
from repositories.user_repository import UserRepository
from schemas.user import UserUpdate


class UserService:
    """Business logic around reading/updating/deleting users."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_by_id_or_raise(self, user_id: int) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with id '{user_id}' not found.")
        return user

    async def list_users(self, offset: int = 0, limit: int = 50) -> list[User]:
        return await self._repository.list_all(offset=offset, limit=limit)

    async def update_user(self, user_id: int, data: UserUpdate, *, allow_role_change: bool) -> User:
        user = await self.get_by_id_or_raise(user_id)

        update_data = data.model_dump(exclude_unset=True)
        if not allow_role_change:
            update_data.pop("role", None)

        for field, value in update_data.items():
            setattr(user, field, value)

        return await self._repository.save(user)

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_by_id_or_raise(user_id)
        await self._repository.delete(user)