# app/api/routes/users.py
from typing import List

from app.schemas.users import (
    CheckUserExistsResponseSchema,
    RegisterRequestSchema,
    RegisterResponseSchema,
    UpdateUserRequestSchema,
    UseExistRequestSchema,
)
from app.service.users import UserService
import uuid
import traceback

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.users import (
    CreateUserDetailRequest,
    UpdateUserDetailRequest,
    UserDetailResponse,
)
from app.service.users import UserDetailService
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log


router = APIRouter(prefix="/users")


@router.get(
    "/exists",
    response_model=CheckUserExistsResponseSchema,
    status_code=status.HTTP_200_OK,
tags=["Users"]
)
async def check_user_exists(
    payload: UseExistRequestSchema = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    exists = await UserService(db).check_exists(payload.phone_number)
    return CheckUserExistsResponseSchema(exists=exists)


@router.post(
    "",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
tags=["Users"]
)
async def create_user(
    payload: RegisterRequestSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Register a new user (phone + password)."""
    try:
        user = await UserService(db).create(payload)
        return user

    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create user: {e}. {traceback.format_exc()}",
        )


@router.get(
    "",
    response_model=List[RegisterResponseSchema],
    status_code=status.HTTP_200_OK,
tags=["Users"]
)
async def get_all_users(
    db: AsyncSession = Depends(get_async_db),
):
    """List all users."""
    try:
        users = await UserService(db).list_all()
        return users

    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list users: {e}. {traceback.format_exc()}",
        )


@router.get(
    "/{user_id}",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_200_OK,
tags=["Users"]
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a single user by UUID."""
    try:
        user = await UserService(db).get_one(user_id)
        return user

    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get user: {e}. {traceback.format_exc()}",
        )


@router.patch(
    "/{user_id}",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_200_OK,
tags=["Users"]
)
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequestSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing user."""
    try:
        user = await UserService(db).update(user_id, payload)
        return user

    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to update user: {e}. {traceback.format_exc()}",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
tags=["Users"]
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a user by UUID."""
    try:
        await UserService(db).delete(user_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete user: {e}. {traceback.format_exc()}",
        )

@router.post(
    "_details",
    response_model=UserDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["User Details"],
)
async def create_user_detail(
    user_id: uuid.UUID,
    payload: CreateUserDetailRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        detail = await UserDetailService(db).create(user_id, payload)
        return detail
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create user details: {e}. {traceback.format_exc()}",
        )


@router.get(
    "_details",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["User Details"],

)
async def get_user_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await UserDetailService(db).get(user_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to fetch user details: {e}. {traceback.format_exc()}",
        )


@router.patch(
    "_details",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["User Details"],

)
async def update_user_detail(
    user_id: uuid.UUID,
    payload: UpdateUserDetailRequest,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await UserDetailService(db).update(user_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to update user details: {e}. {traceback.format_exc()}",
        )


@router.delete(
    "_details",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["User Details"],

)
async def delete_user_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        await UserDetailService(db).delete(user_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete user details: {e}. {traceback.format_exc()}",
        )
