import uuid, traceback
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.hospitals import HospitalService
from app.schemas.hospitals import (
    HospitalCreateSchema,
    HospitalUpdateSchema,
    HospitalResponseSchema,
)
import base64
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from fastapi import Depends
from app.core.security import get_current_user
from app.models.users import UserModel

router = APIRouter(
    prefix="/hospitals",
    tags=["Locations - Hospitals"],
)


@router.get(
    "",
    response_model=List[HospitalResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_hospitals(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """List all hospitals."""
    try:
        return await HospitalService(db).list_hospitals()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list hospitals: {e}",
        )


@router.get(
    "/{hospital_id}",
    response_model=HospitalResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get a single hospital by ID."""
    try:
        return await HospitalService(db).get_hospital(hospital_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get hospital: {e}",
        )


@router.post(
    "",
    response_model=HospitalResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_hospital(
    payload: HospitalCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        return await HospitalService(db).create_hospital(payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create hospital: {e}",
        )


@router.patch(
    "/{hospital_id}",
    response_model=HospitalResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_hospital(
    hospital_id: uuid.UUID,
    payload: HospitalUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an existing hospital."""
    try:
        return await HospitalService(db).update_hospital(hospital_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to update hospital: {e}",
        )


@router.delete(
    "/{hospital_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hospital(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a hospital."""
    try:
        await HospitalService(db).delete_hospital(hospital_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete hospital: {e}",
        )


@router.post(
    "/{hospital_id}/photo",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def upload_hospital_photo(
    hospital_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Read bytes, Base64-encode & save as TEXT."""
    data = await file.read()
    await HospitalService(db).upload_photo(hospital_id, data)


@router.get(
    "/{hospital_id}/photo",
    status_code=status.HTTP_200_OK,
)
async def get_hospital_photo(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    b64 = await HospitalService(db).get_photo(hospital_id)
    return JSONResponse(content={"photo": b64})


@router.delete(
    "/{hospital_id}/photo",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hospital_photo(
    hospital_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        await HospitalService(db).delete_photo(hospital_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete hospital photo: {e}",
        )
