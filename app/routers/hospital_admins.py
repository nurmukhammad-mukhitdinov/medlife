import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.hospital_admins import (
    HospitalAdminCreateSchema,
    HospitalAdminUpdateSchema,
    HospitalAdminResponseSchema,
)
from app.service.hospital_admins import HospitalAdminService

router = APIRouter(tags=["Hospital Admins"], prefix="/hospital-admins")


@router.post("", response_model=HospitalAdminResponseSchema, status_code=201)
async def create_hospital_admin(
    payload: HospitalAdminCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    return await HospitalAdminService(db).create(payload)


@router.patch("/{admin_id}", response_model=HospitalAdminResponseSchema)
async def update_hospital_admin(
    admin_id: uuid.UUID,
    payload: HospitalAdminUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    return await HospitalAdminService(db).update(admin_id, payload)


@router.delete("/{admin_id}")
async def delete_hospital_admin(
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    return await HospitalAdminService(db).delete(admin_id)


@router.get("", response_model=list[HospitalAdminResponseSchema])
async def get_all_hospital_admins(
    db: AsyncSession = Depends(get_async_db),
):
    return await HospitalAdminService(db).get_all()


@router.get("/{admin_id}", response_model=HospitalAdminResponseSchema)
async def get_hospital_admin(
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    return await HospitalAdminService(db).get_by_id(admin_id)
