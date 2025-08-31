import uuid
import traceback
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models.users import UserModel
from app.exc import LoggedHTTPException, raise_with_log

from app.service.reviews import ReviewService
from app.schemas.reviews import (
    ReviewCreateSchema,
    ReviewUpdateSchema,
    ReviewResponseSchema,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "", response_model=List[ReviewResponseSchema], status_code=status.HTTP_200_OK
)
async def get_all_reviews(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).list_all()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to list reviews: {e}")


@router.get(
    "/by-user/{user_id}",
    response_model=List[ReviewResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_reviews_by_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).list_by_user(user_id=user_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to list user reviews: {e}")


@router.get(
    "/by-hospital/{hospital_id}",
    response_model=List[ReviewResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_reviews_by_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).list_by_hospital(hospital_id=hospital_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to list hospital reviews: {e}")


@router.get("/{review_id}", response_model=ReviewResponseSchema, status_code=status.HTTP_200_OK)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).get_one(review_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to get review: {e}")


@router.post("", response_model=ReviewResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).create(payload, current_user)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create review: {e}")


@router.patch("/{review_id}", response_model=ReviewResponseSchema, status_code=status.HTTP_200_OK)
async def update_review(
    review_id: uuid.UUID,
    payload: ReviewUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await ReviewService(db).update(review_id, payload, current_user)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to update review: {e}")


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        await ReviewService(db).delete(review_id, current_user)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to delete review: {e}")
