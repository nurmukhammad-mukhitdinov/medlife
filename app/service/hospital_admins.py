# app/service/hospital_admins.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models import UserModel, HospitalModel
from app.core.security import hash_password
from app.schemas.hospital_admins import HospitalAdminResponseSchema

HOSPITAL_ADMIN_ROLE_ID = uuid.UUID("8497eb6c-0eea-40e7-8467-f8e393f56822")


class HospitalAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data):
        hospital = await self.db.get(HospitalModel, data.hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        if hospital.admin_id:
            raise HTTPException(status_code=400, detail="Hospital already has an admin")

        # create user
        user = UserModel(
            phone_number=data.phone_number,
            hashed_password=hash_password(data.password),
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role_id=HOSPITAL_ADMIN_ROLE_ID,
        )
        self.db.add(user)
        await self.db.flush()  # populate user.id

        # link to hospital
        hospital.admin_id = user.id
        self.db.add(hospital)

        await self.db.commit()

        # return DTO with hospital_id
        return HospitalAdminResponseSchema.model_validate({
            "id": user.id,
            "phone_number": user.phone_number,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "hospital_id": hospital.id,
        })

    async def update(self, admin_id: uuid.UUID, data):
        admin = await self.db.get(UserModel, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Hospital admin not found")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(admin, field, value)

        await self.db.flush()

        # find hospital for this admin (LEFT JOIN)
        res = await self.db.execute(
            select(HospitalModel.id).where(HospitalModel.admin_id == admin_id)
        )
        hospital_id = res.scalar()

        await self.db.commit()

        return HospitalAdminResponseSchema.model_validate({
            "id": admin.id,
            "phone_number": admin.phone_number,
            "email": admin.email,
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "hospital_id": hospital_id,
        })

    async def delete(self, admin_id: uuid.UUID):
        admin = await self.db.get(UserModel, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Hospital admin not found")

        res = await self.db.execute(
            select(HospitalModel).where(HospitalModel.admin_id == admin_id)
        )
        hospital = res.scalars().first()
        if hospital:
            hospital.admin_id = None
            self.db.add(hospital)

        await self.db.delete(admin)
        await self.db.commit()
        return {"detail": "Hospital admin deleted"}

    async def get_all(self):
        result = await self.db.execute(
            select(UserModel, HospitalModel.id.label("hospital_id"))
            .join(HospitalModel, HospitalModel.admin_id == UserModel.id, isouter=True)
            .where(UserModel.role_id == HOSPITAL_ADMIN_ROLE_ID)
        )
        rows = result.all()
        return [
            HospitalAdminResponseSchema.model_validate({
                "id": u.id,
                "phone_number": u.phone_number,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "hospital_id": h_id,
            })
            for (u, h_id) in rows
        ]

    async def get_by_id(self, admin_id: uuid.UUID):
        result = await self.db.execute(
            select(UserModel, HospitalModel.id.label("hospital_id"))
            .join(HospitalModel, HospitalModel.admin_id == UserModel.id, isouter=True)
            .where(UserModel.id == admin_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Hospital admin not found")

        u, h_id = row
        return HospitalAdminResponseSchema.model_validate({
            "id": u.id,
            "phone_number": u.phone_number,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "hospital_id": h_id,
        })
