# app/api/routes/users.py
import uuid
import traceback
from typing import List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.users import (
    CheckUserExistsResponseSchema,
    RegisterRequestSchema,
    RegisterResponseSchema,
    UpdateUserRequestSchema,
    UseExistRequestSchema,
)
from app.service.users import UserService
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/exists",
    response_model=CheckUserExistsResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def check_user_exists(
    payload: UseExistRequestSchema = Depends(),
    db: AsyncSession               = Depends(get_async_db),
):
    exists = await UserService(db).check_exists(payload.phone_number)
    return CheckUserExistsResponseSchema(exists=exists)


@router.post(
    "",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
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
