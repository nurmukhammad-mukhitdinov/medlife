import uuid, traceback
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.doctors import DoctorService
from app.schemas.doctors import (
    DoctorCreateSchema,
    DoctorUpdateSchema,
    DoctorResponseSchema,
)
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get(
    "",
    response_model=List[DoctorResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_doctors(db: AsyncSession = Depends(get_async_db)):
    """List all doctors."""
    try:
        return await DoctorService(db).list_doctors()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list doctors: {e}",
        )


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a single doctor by ID."""
    try:
        return await DoctorService(db).get_doctor(doctor_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get doctor: {e}",
        )


@router.post(
    "",
    response_model=DoctorResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    payload: DoctorCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new doctor."""
    try:
        return await DoctorService(db).create_doctor(payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create doctor: {e}",
        )


@router.patch(
    "/{doctor_id}",
    response_model=DoctorResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing doctor."""
    try:
        return await DoctorService(db).update_doctor(doctor_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to update doctor: {e}",
        )


@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a doctor."""
    try:
        await DoctorService(db).delete_doctor(doctor_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete doctor: {e}",
        )
