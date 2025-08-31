import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reviews import ReviewsModel
from app.models.hospitals import HospitalModel
from app.models.users import UserModel
from app.schemas.reviews import (
    ReviewCreateSchema,
    ReviewUpdateSchema,
    ReviewResponseSchema,
)


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- helpers ----------
    @staticmethod
    def _display_name(user: UserModel | None) -> str | None:
        if not user:
            return None
        first = (user.first_name or "").strip()
        last = (user.last_name or "").strip()
        full = " ".join(x for x in (first, last) if x)
        return full or None

    def _to_response(self, r: ReviewsModel) -> ReviewResponseSchema:
        return ReviewResponseSchema(
            id=r.id,
            user_id=r.user_id,
            user_name=self._display_name(getattr(r, "user", None)),
            hospital_id=r.hospital_id,
            comment=r.comment,
        )

    async def _ensure_hospital(self, hospital_id: uuid.UUID) -> None:
        if not await self.db.get(HospitalModel, hospital_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Hospital not found")

    async def _ensure_user(self, user_id: uuid.UUID) -> None:
        if not await self.db.get(UserModel, user_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    async def _ensure_owner(self, review: ReviewsModel, user: UserModel) -> None:
        if str(review.user_id) != str(user.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")

    # ---------- reads ----------
    async def get_one(self, review_id: uuid.UUID) -> ReviewResponseSchema:
        stmt = (
            select(ReviewsModel)
            .where(ReviewsModel.id == review_id)
            .options(selectinload(ReviewsModel.user))
        )
        res = await self.db.execute(stmt)
        review = res.scalars().first()
        if not review:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
        return self._to_response(review)

    async def list_all(self) -> List[ReviewResponseSchema]:
        stmt = select(ReviewsModel).options(selectinload(ReviewsModel.user)).order_by(ReviewsModel.id.desc())
        items = (await self.db.execute(stmt)).scalars().all()
        return [self._to_response(x) for x in items]

    async def list_by_user(self, *, user_id: uuid.UUID) -> List[ReviewResponseSchema]:
        await self._ensure_user(user_id)
        stmt = (
            select(ReviewsModel)
            .where(ReviewsModel.user_id == user_id)
            .options(selectinload(ReviewsModel.user))
            .order_by(ReviewsModel.id.desc())
        )
        items = (await self.db.execute(stmt)).scalars().all()
        return [self._to_response(x) for x in items]

    async def list_by_hospital(self, *, hospital_id: uuid.UUID) -> List[ReviewResponseSchema]:
        await self._ensure_hospital(hospital_id)
        stmt = (
            select(ReviewsModel)
            .where(ReviewsModel.hospital_id == hospital_id)
            .options(selectinload(ReviewsModel.user))
            .order_by(ReviewsModel.id.desc())
        )
        items = (await self.db.execute(stmt)).scalars().all()
        return [self._to_response(x) for x in items]

    # ---------- writes ----------
    async def create(self, data: ReviewCreateSchema, current_user: UserModel) -> ReviewResponseSchema:
        await self._ensure_hospital(data.hospital_id)

        entity = ReviewsModel(
            user_id=current_user.id,
            hospital_id=data.hospital_id,
            comment=data.comment,
        )
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)

        # attach for display name without another query
        entity.user = current_user
        return self._to_response(entity)

    async def update(
        self,
        review_id: uuid.UUID,
        data: ReviewUpdateSchema,
        current_user: UserModel,
    ) -> ReviewResponseSchema:
        stmt = (
            select(ReviewsModel)
            .where(ReviewsModel.id == review_id)
            .options(selectinload(ReviewsModel.user))
        )
        res = await self.db.execute(stmt)
        entity = res.scalars().first()
        if not entity:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")

        await self._ensure_owner(entity, current_user)

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(entity, k, v)

        await self.db.flush()
        await self.db.refresh(entity)
        return self._to_response(entity)

    async def delete(self, review_id: uuid.UUID, current_user: UserModel) -> None:
        entity = await self.db.get(ReviewsModel, review_id)
        if not entity:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
        await self._ensure_owner(entity, current_user)

        await self.db.delete(entity)
        await self.db.flush()
