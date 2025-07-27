# app/services/location_service.py
import uuid
import traceback

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.locations import RegionModel, DistrictModel
from app.schemas.locations import (
    RegionCreateSchema,
    RegionUpdateSchema,
    DistrictCreateSchema,
    DistrictUpdateSchema,
)
from app.exc import LoggedHTTPException


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    #
    # ─── REGIONS ──────────────────────────────────────────────────────────────
    #

    async def list_regions(self) -> list[RegionModel]:
        stmt = select(RegionModel)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_region(self, region_id: uuid.UUID) -> RegionModel:
        stmt = (
            select(RegionModel)
            .where(RegionModel.id == region_id)
            .options(selectinload(RegionModel.districts))
        )
        res = await self.db.execute(stmt)
        region = res.scalars().first()
        if not region:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Region not found")
        return region

    async def create_region(self, payload: RegionCreateSchema) -> RegionModel:
        # no duplicate-name check here, but you could add one if you like
        region = RegionModel(name=payload.name)
        self.db.add(region)
        await self.db.flush()
        return region

    async def update_region(
        self, region_id: uuid.UUID, payload: RegionUpdateSchema
    ) -> RegionModel:
        region = await self.get_region(region_id)
        if payload.name is not None:
            region.name = payload.name
        await self.db.flush()
        return region

    async def delete_region(self, region_id: uuid.UUID) -> None:
        region = await self.get_region(region_id)
        await self.db.delete(region)
        await self.db.flush()

    #
    # ─── DISTRICTS ────────────────────────────────────────────────────────────
    #

    async def list_districts(self) -> list[DistrictModel]:
        stmt = select(DistrictModel).options(selectinload(DistrictModel.region))
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def list_districts_by_region(
        self, region_id: uuid.UUID
    ) -> list[DistrictModel]:
        # ensure region exists
        await self.get_region(region_id)
        stmt = (
            select(DistrictModel)
            .where(DistrictModel.region_id == region_id)
            .options(selectinload(DistrictModel.region))
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_district(self, district_id: uuid.UUID) -> DistrictModel:
        stmt = (
            select(DistrictModel)
            .where(DistrictModel.id == district_id)
            .options(selectinload(DistrictModel.region))
        )
        res = await self.db.execute(stmt)
        district = res.scalars().first()
        if not district:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "District not found")
        return district

    async def create_district(self, payload: DistrictCreateSchema) -> DistrictModel:
        # ensure region exists
        await self.get_region(payload.region_id)
        district = DistrictModel(name=payload.name, region_id=payload.region_id)
        self.db.add(district)
        await self.db.flush()

        # now re‑fetch with region relationship eagerly loaded
        return await self.get_district(district.id)

    async def update_district(
        self, district_id: uuid.UUID, payload: DistrictUpdateSchema
    ) -> DistrictModel:
        district = await self.get_district(district_id)
        if payload.name is not None:
            district.name = payload.name
        if payload.region_id is not None:
            # ensure new region exists
            await self.get_region(payload.region_id)
            district.region_id = payload.region_id
        await self.db.flush()
        return district

    async def delete_district(self, district_id: uuid.UUID) -> None:
        district = await self.get_district(district_id)
        await self.db.delete(district)
        await self.db.flush()
