import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hospitals import HospitalModel
from app.schemas.hospitals import HospitalCreateSchema, HospitalUpdateSchema
from app.exc import LoggedHTTPException
import base64


class HospitalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_hospitals(self) -> list[HospitalModel]:
        stmt = select(HospitalModel).options(
            selectinload(HospitalModel.region),
            selectinload(HospitalModel.district),
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_hospital(self, hospital_id: uuid.UUID) -> HospitalModel:
        stmt = (
            select(HospitalModel)
            .where(HospitalModel.id == hospital_id)
            .options(
                selectinload(HospitalModel.region),
                selectinload(HospitalModel.district),
            )
        )
        res = await self.db.execute(stmt)
        hospital = res.scalars().first()
        if not hospital:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Hospital not found")
        return hospital

    async def create_hospital(self, payload: HospitalCreateSchema) -> HospitalModel:
        hosp = HospitalModel(
            name=payload.name,
            address=payload.address,
            orientir=payload.orientir,
            region_id=payload.region_id,
            district_id=payload.district_id,
            reyting=payload.reyting if hasattr(payload, "reyting") else 5.00,
        )
        self.db.add(hosp)
        await self.db.flush()
        return await self.get_hospital(hosp.id)

    async def update_hospital(
        self, hospital_id: uuid.UUID, payload: HospitalUpdateSchema
    ) -> HospitalModel:
        hosp = await self.get_hospital(hospital_id)
        if payload.name is not None:
            hosp.name = payload.name
        if payload.address is not None:
            hosp.address = payload.address
        if payload.orientir is not None:
            hosp.orientir = payload.orientir
        if payload.region_id is not None:
            hosp.region_id = payload.region_id
        if payload.district_id is not None:
            hosp.district_id = payload.district_id
        await self.db.flush()
        return await self.get_hospital(hospital_id)

    async def delete_hospital(self, hospital_id: uuid.UUID) -> None:
        hosp = await self.get_hospital(hospital_id)
        await self.db.delete(hosp)
        await self.db.flush()

    async def upload_photo(self, hospital_id: uuid.UUID, data: bytes):
        """Store as Base64 text."""
        hosp = await self.get_hospital(hospital_id)
        hosp.photo = base64.b64encode(data).decode("ascii")
        await self.db.flush()

    async def get_photo(self, hospital_id: uuid.UUID) -> str:
        """Return the Base64 text (or empty string)."""
        hosp = await self.get_hospital(hospital_id)
        return hosp.photo or ""

    async def delete_photo(self, hospital_id: uuid.UUID) -> None:
        """Remove the stored Base64 photo."""
        hosp = await self.get_hospital(hospital_id)
        hosp.photo = None
        await self.db.flush()
