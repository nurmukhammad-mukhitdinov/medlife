# app/services/user_service.py
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import UserModel
from app.core.security import hash_password
from app.schemas.users import RegisterRequestSchema, UpdateUserRequestSchema


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
