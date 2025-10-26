# app/services/lawyers.py
from app.core.security import hash_password
from app.schemas.users import RegisterRequestSchema, UpdateUserRequestSchema

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.lawyers import UserModelLawyer, LawyerModelLawyer
from app.schemas.lawyers import (
    LawyerCreate, LawyerUpdate,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_exists(self, phone_number: str) -> bool:
        stmt = select(UserModelLawyer).where(UserModelLawyer.phone_number == phone_number)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def create(self, payload: RegisterRequestSchema) -> UserModelLawyer:
        if await self.check_exists(payload.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

        user = UserModelLawyer(
            phone_number=payload.phone_number,
            hashed_password=hash_password(payload.password),
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role_id=None,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        # optionally: await self.db.commit()
        return user

    async def get_one(self, user_id: uuid.UUID) -> UserModelLawyer:
        stmt = select(UserModelLawyer).where(UserModelLawyer.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def list_all(self) -> list[UserModelLawyer]:
        stmt = select(UserModelLawyer)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        user_id: uuid.UUID,
        payload: UpdateUserRequestSchema,
    ) -> UserModelLawyer:
        user = await self.get_one(user_id)
        # apply only provided fields
        if payload.phone_number is not None:
            user.phone_number = payload.phone_number
        if payload.password is not None:
            user.hashed_password = hash_password(payload.password)
        if payload.email is not None:
            user.email = payload.email
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name

        await self.db.flush()
        return user

    async def delete(self, user_id: uuid.UUID) -> None:
        user = await self.get_one(user_id)
        await self.db.delete(user)
        await self.db.flush()


class LawyerCrudService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _by_id(self, lawyer_id: uuid.UUID) -> LawyerModelLawyer:
        stmt = select(LawyerModelLawyer).where(LawyerModelLawyer.id == lawyer_id)
        obj = (await self.db.execute(stmt)).scalars().first()
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found",
            )
        return obj

    async def create(self, payload: LawyerCreate, *, commit: bool = False) -> LawyerModelLawyer:
        obj = LawyerModelLawyer(
            user_id=payload.user_id,
            description=payload.description,
            cases_participated=payload.cases_participated or 0,
            cases_won=payload.cases_won or 0,
            license_number=payload.license_number,
            license_is_active=False if payload.license_is_active is None else payload.license_is_active,
            license_issued_at=payload.license_issued_at,
            license_expires_at=payload.license_expires_at,
            career_timeline=payload.career_timeline,
            specializations=payload.specializations,
            experience_years=payload.experience_years,
            photos=payload.photos,
            region_id=payload.region_id,
            district_id=payload.district_id,
            organization_name=payload.organization_name,
            phone_number=payload.phone_number,
            is_phone_reachable=True if payload.is_phone_reachable is None else payload.is_phone_reachable,
            mini_call_center_id=payload.mini_call_center_id,
            is_active=True if payload.is_active is None else payload.is_active,
        )
        self.db.add(obj)
        await self.db.flush()
        if commit:
            await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, lawyer_id: uuid.UUID) -> LawyerModelLawyer:
        return await self._by_id(lawyer_id)

    async def update(self, lawyer_id: uuid.UUID, payload: LawyerUpdate, *, commit: bool = False) -> LawyerModelLawyer:
        obj = await self._by_id(lawyer_id)

        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)

        await self.db.flush()
        if commit:
            await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, lawyer_id: uuid.UUID, *, commit: bool = False) -> None:
        obj = await self._by_id(lawyer_id)
        await self.db.delete(obj)
        await self.db.flush()
        if commit:
            await self.db.commit()
