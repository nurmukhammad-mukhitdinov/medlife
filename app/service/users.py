# app/services/user_service.py
from app.core.security import hash_password
from app.schemas.users import RegisterRequestSchema, UpdateUserRequestSchema
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import UserModel, UserDetailModel
from app.models.locations import RegionModel, DistrictModel
from app.schemas.users import (
    CreateUserDetailRequest,
    UpdateUserDetailRequest,
    UserDetailResponse,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_exists(self, phone_number: str) -> bool:
        stmt = select(UserModel).where(UserModel.phone_number == phone_number)
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None

    async def create(self, payload: RegisterRequestSchema) -> UserModel:
        # 1) no dupes
        if await self.check_exists(payload.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

        # 2) build & persist
        user = UserModel(
            phone_number=payload.phone_number,
            hashed_password=hash_password(payload.password),
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role_id="8497eb6c-0eea-40e7-8467-f8e393f56811",
        )
        self.db.add(user)
        await self.db.flush()  # populate id & created_at
        return user

    async def get_one(self, user_id: uuid.UUID) -> UserModel:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def list_all(self) -> list[UserModel]:
        stmt = select(UserModel)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        user_id: uuid.UUID,
        payload: UpdateUserRequestSchema,
    ) -> UserModel:
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


class UserDetailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _build_response(self, detail: UserDetailModel) -> UserDetailResponse:
        # fetch region name
        region_name = None
        if detail.region_id:
            region = await self.db.get(RegionModel, detail.region_id)
            region_name = region.name if region else None

        # fetch district name
        district_name = None
        if detail.district_id:
            district = await self.db.get(DistrictModel, detail.district_id)
            district_name = district.name if district else None

        return UserDetailResponse(
            id=detail.id,
            user_id=detail.user_id,
            region_id=detail.region_id,
            region_name=region_name,
            district_id=detail.district_id,
            district_name=district_name,
            height_cm=detail.height_cm,
            weight_kg=detail.weight_kg,
            blood_sugar_mg_dl=detail.blood_sugar_mg_dl,
            bp_systolic_mm_hg=detail.bp_systolic_mm_hg,
            bp_diastolic_mm_hg=detail.bp_diastolic_mm_hg,
            cholesterol_mg_dl=detail.cholesterol_mg_dl,
            hemoglobin_g_dl=detail.hemoglobin_g_dl,
            created_at=detail.created_at,
        )

    async def create(
        self,
        user_id: uuid.UUID,
        payload: CreateUserDetailRequest,
    ) -> UserDetailResponse:
        # 1️⃣ ensure user exists
        if not await self.db.get(UserModel, user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 2️⃣ prevent duplicate
        existing = (
            (
                await self.db.execute(
                    select(UserDetailModel).where(UserDetailModel.user_id == user_id)
                )
            )
            .scalars()
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User details already exist",
            )

        # 3️⃣ create & flush
        detail = UserDetailModel(
            user_id=user_id,
            region_id=payload.region_id,
            district_id=payload.district_id,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            blood_sugar_mg_dl=payload.blood_sugar_mg_dl,
            bp_systolic_mm_hg=payload.bp_systolic_mm_hg,
            bp_diastolic_mm_hg=payload.bp_diastolic_mm_hg,
            cholesterol_mg_dl=payload.cholesterol_mg_dl,
            hemoglobin_g_dl=payload.hemoglobin_g_dl,
        )
        self.db.add(detail)
        await self.db.flush()

        # 4️⃣ return with names
        return await self._build_response(detail)

    async def get(self, user_id: uuid.UUID) -> UserDetailResponse:
        detail = (
            (
                await self.db.execute(
                    select(UserDetailModel).where(UserDetailModel.user_id == user_id)
                )
            )
            .scalars()
            .first()
        )
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details not found",
            )
        return await self._build_response(detail)

    async def update(
        self,
        user_id: uuid.UUID,
        payload: UpdateUserDetailRequest,
    ) -> UserDetailResponse:
        detail = (
            (
                await self.db.execute(
                    select(UserDetailModel).where(UserDetailModel.user_id == user_id)
                )
            )
            .scalars()
            .first()
        )
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details not found",
            )

        # apply only provided fields
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(detail, field, value)
        await self.db.flush()

        return await self._build_response(detail)

    async def delete(self, user_id: uuid.UUID) -> None:
        detail = (
            (
                await self.db.execute(
                    select(UserDetailModel).where(UserDetailModel.user_id == user_id)
                )
            )
            .scalars()
            .first()
        )
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User details not found",
            )
        await self.db.delete(detail)
        await self.db.flush()
