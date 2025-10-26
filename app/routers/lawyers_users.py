# app/api/routes/user_lawyers.py
from typing import List

from app.schemas.users import (
    CheckUserExistsResponseSchema,
    RegisterRequestSchema,
    RegisterResponseSchema,
    UpdateUserRequestSchema,
    UseExistRequestSchema,
)
from app.service.lawyers import UserService
import uuid
import traceback

from app.exc import LoggedHTTPException, raise_with_log
from app.core.security import verify_password, create_access_token
from app.schemas.users import SignInRequestSchema, SignInResponseSchema
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from fastapi import Depends

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token
from app.models.users import UserModel
from app.core.security import get_current_user

from app.core.database import get_async_db
from app.schemas.users import SignInResponseSchema

router = APIRouter(prefix="/users_lawyers")


@router.get(
    "/exists",
    response_model=CheckUserExistsResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Users Lawyers"],
)
async def check_user_exists(
    payload: UseExistRequestSchema = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    exists = await UserService(db).check_exists(payload.phone_number)
    return CheckUserExistsResponseSchema(exists=exists)


@router.post(
    "/login",
    response_model=SignInResponseSchema,
    status_code=status.HTTP_200_OK,
    tags=["Users Lawyers"],
)
async def login(
    credentials: SignInRequestSchema,
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(UserModel).where(UserModel.phone_number == credentials.phone_number)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_at = create_access_token(data={"sub": str(user.id)})

    return SignInResponseSchema(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
    )


@router.post(
    "/auth/token",
    response_model=SignInResponseSchema,
    tags=["Users Lawyers"],
)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(UserModel).where(UserModel.phone_number == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    access_token, expires_at = create_access_token(data={"sub": str(user.id)})
    return SignInResponseSchema(
        access_token=access_token, token_type="bearer", expires_at=expires_at
    )


@router.post(
    "",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Users Lawyers"],
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
    tags=["Users Lawyers"],
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
    tags=["Users Lawyers"],
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
    tags=["Users Lawyers"],
)
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequestSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users Lawyers"],
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
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
