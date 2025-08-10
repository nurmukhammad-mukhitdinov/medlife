import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from fastapi import HTTPException, status

from app.models.service_prices import ServiceModel  # adjust import path if different
from app.models import HospitalModel, DoctorModel  # if you expose these via __init__
from app.schemas.service_prices import (
    ServicePriceCreate,
    ServicePriceUpdate,
)


class ServicePriceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _validate_owner_exists(
        self, hospital_id: Optional[uuid.UUID], doctor_id: Optional[uuid.UUID]
    ) -> None:
        # At least one must exist (schema enforces), ensure FK objects exist if provided
        if hospital_id is not None:
            hospital = await self.db.get(HospitalModel, hospital_id)
            if not hospital:
                raise HTTPException(status_code=404, detail="Hospital not found")
        if doctor_id is not None:
            doctor = await self.db.get(DoctorModel, doctor_id)
            if not doctor:
                raise HTTPException(status_code=404, detail="Doctor not found")

    async def create(self, data: ServicePriceCreate) -> ServiceModel:
        await self._validate_owner_exists(data.hospital_id, data.doctor_id)

        entity = ServiceModel(
            name=data.name,
            description=data.description,
            price=data.price,
            hospital_id=data.hospital_id,
            doctor_id=data.doctor_id,
        )
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update(
        self, service_id: uuid.UUID, data: ServicePriceUpdate
    ) -> ServiceModel:
        entity = await self.db.get(ServiceModel, service_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Service not found")

        # If owner fields are present in payload, validate existence
        payload = data.dict(exclude_unset=True)
        if "hospital_id" in payload or "doctor_id" in payload:
            hospital_id = payload.get("hospital_id", entity.hospital_id)
            doctor_id = payload.get("doctor_id", entity.doctor_id)
            if hospital_id is None and doctor_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Either hospital_id or doctor_id must be provided.",
                )
            await self._validate_owner_exists(hospital_id, doctor_id)

        for k, v in payload.items():
            setattr(entity, k, v)

        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, service_id: uuid.UUID) -> dict:
        entity = await self.db.get(ServiceModel, service_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Service not found")
        await self.db.delete(entity)
        await self.db.commit()
        return {"detail": "Service deleted"}

    async def get_by_id(self, service_id: uuid.UUID) -> ServiceModel:
        entity = await self.db.get(ServiceModel, service_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Service not found")
        return entity

    async def list(
        self,
        hospital_id: Optional[uuid.UUID] = None,
        doctor_id: Optional[uuid.UUID] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list[ServiceModel], int]:
        query = select(ServiceModel)
        count_query = select(func.count(ServiceModel.id))

        # Filters
        conditions = []
        if hospital_id:
            conditions.append(ServiceModel.hospital_id == hospital_id)
        if doctor_id:
            conditions.append(ServiceModel.doctor_id == doctor_id)
        if q:
            like = f"%{q.strip()}%"
            conditions.append(
                or_(ServiceModel.name.ilike(like), ServiceModel.description.ilike(like))
            )

        if conditions:
            query = query.filter(*conditions)
            count_query = count_query.filter(*conditions)

        # Total count
        total = (await self.db.execute(count_query)).scalar_one()
        # Pagination
        query = query.order_by(ServiceModel.name.asc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        items = result.scalars().all()
        return items, total
