import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctors import DoctorModel
from app.schemas.doctors import DoctorCreateSchema, DoctorUpdateSchema
from app.exc import LoggedHTTPException
from app.exc import LoggedHTTPException
import base64

class DoctorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_doctors(self) -> list[DoctorModel]:
        stmt = select(DoctorModel).options(selectinload(DoctorModel.hospital))
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_doctor(self, doctor_id: uuid.UUID) -> DoctorModel:
        stmt = (
            select(DoctorModel)
            .where(DoctorModel.id == doctor_id)
            .options(selectinload(DoctorModel.hospital))
        )
        res = await self.db.execute(stmt)
        doctor = res.scalars().first()
        if not doctor:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
        return doctor

    async def create_doctor(self, payload: DoctorCreateSchema) -> DoctorModel:
        # build + flush
        doc = DoctorModel(
            first_name=payload.first_name,
            last_name=payload.last_name,
            professional=payload.professional,
            about=payload.about,
            hospital_id=payload.hospital_id,
            reyting=payload.reyting if hasattr(payload, 'reyting') else 5.00,

        )
        self.db.add(doc)
        await self.db.flush()
        # re-fetch with hospital loaded
        return await self.get_doctor(doc.id)

    async def update_doctor(
        self, doctor_id: uuid.UUID, payload: DoctorUpdateSchema
    ) -> DoctorModel:
        doc = await self.get_doctor(doctor_id)
        if payload.first_name is not None:
            doc.first_name = payload.first_name
        if payload.last_name is not None:
            doc.last_name = payload.last_name
        if payload.professional is not None:
            doc.professional = payload.professional
        if payload.about is not None:
            doc.about = payload.about
        if payload.hospital_id is not None:
            doc.hospital_id = payload.hospital_id
        await self.db.flush()
        return await self.get_doctor(doctor_id)

    async def delete_doctor(self, doctor_id: uuid.UUID) -> None:
        doc = await self.get_doctor(doctor_id)
        await self.db.delete(doc)
        await self.db.flush()

    async def upload_photo(self, doctor_id: uuid.UUID, data: bytes):
        """Base64-encode & save as TEXT."""
        doc = await self.get_doctor(doctor_id)
        doc.photo = base64.b64encode(data).decode("ascii")
        await self.db.flush()

    async def get_photo(self, doctor_id: uuid.UUID) -> str:
        """Return stored Base64 string (or empty)."""
        doc = await self.get_doctor(doctor_id)
        return doc.photo or ""

    async def delete_photo(self, doctor_id: uuid.UUID) -> None:
        """Remove the stored Base64 photo."""
        doc = await self.get_doctor(doctor_id)
        doc.photo = None
        await self.db.flush()