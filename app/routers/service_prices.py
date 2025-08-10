import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.service.service_prices import ServicePriceService
from app.schemas.service_prices import (
    ServicePriceCreate,
    ServicePriceUpdate,
    ServicePriceResponse,
    ServicePriceListResponse,
)

router = APIRouter(tags=["Service Prices"], prefix="/service-prices")


@router.post(
    "", response_model=ServicePriceResponse, status_code=status.HTTP_201_CREATED
)
async def create_service_price(
    payload: ServicePriceCreate,
    db: AsyncSession = Depends(get_async_db),
):
    return await ServicePriceService(db).create(payload)


@router.patch("/{service_id}", response_model=ServicePriceResponse)
async def update_service_price(
    service_id: uuid.UUID,
    payload: ServicePriceUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    return await ServicePriceService(db).update(service_id, payload)


@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service_price(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    return await ServicePriceService(db).delete(service_id)


@router.get("/{service_id}", response_model=ServicePriceResponse)
async def get_service_price(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    return await ServicePriceService(db).get_by_id(service_id)


@router.get("", response_model=ServicePriceListResponse)
async def list_service_prices(
    hospital_id: Optional[uuid.UUID] = Query(None),
    doctor_id: Optional[uuid.UUID] = Query(None),

    db: AsyncSession = Depends(get_async_db),
):
    items, total = await ServicePriceService(db).list(
        hospital_id=hospital_id,
        doctor_id=doctor_id,

    )
    return {"items": items, "total": total}
