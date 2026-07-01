from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import AdminUser, CurrentUser, get_user_service
from core.exceptions import UserNotFoundError
from models.user import UserRole
from schemas.user import UserResponse, UserUpdate
from services.user_service import UserService

router = APIRouter(tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List users (admin only)",
    description="Returns a paginated list of all users. Requires admin role.",
)
async def list_users(
        _: AdminUser,
        user_service: Annotated[UserService, Depends(get_user_service)],
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
) -> list[UserResponse]:
    users = await user_service.list_users(offset=offset, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (admin only)",
    description="Fetches a single user's profile by ID. Requires admin role.",
)
async def get_user(
        user_id: int,
        _: AdminUser,
        user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        user = await user_service.get_by_id_or_raise(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    return UserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Partially update a user",
    description="Updates one or more fields of a user. Regular users may only update "
                "their own profile and cannot change their role; admins may update anyone and "
                "may change roles.",
)
async def update_user(
        user_id: int,
        data: UserUpdate,
        current_user: CurrentUser,
        user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile.",
        )

    try:
        user = await user_service.update_user(user_id, data, allow_role_change=is_admin)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin only)",
    description="Permanently deletes a user account. Requires admin role.",
)
async def delete_user(
        user_id: int,
        _: AdminUser,
        user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    try:
        await user_service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail) from exc
