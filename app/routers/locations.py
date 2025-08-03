# app/api/routes/locations.py
import uuid
import traceback
from typing import List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.locations import LocationService
from app.schemas.locations import (
    RegionResponseSchema,
    RegionWithDistrictsSchema,
    RegionCreateSchema,
    RegionUpdateSchema,
    DistrictResponseSchema,
    DistrictCreateSchema,
    DistrictUpdateSchema,
)
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log

router = APIRouter(prefix="/locations")


@router.get(
    "/regions",
    tags=["Locations - Regions"],
    response_model=List[RegionResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_regions(db: AsyncSession = Depends(get_async_db)):
    """List all regions."""
    try:
        return await LocationService(db).list_regions()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to list regions: {e}"
        )


@router.get(
    "/regions/{region_id}",
    tags=["Locations - Regions"],
    response_model=RegionWithDistrictsSchema,
    status_code=status.HTTP_200_OK,
)
async def get_region(
    region_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get one region plus its districts."""
    try:
        svc = LocationService(db)
        region = await svc.get_region(region_id)
        # manually attach districts list for the richer schema
        districts = await svc.list_districts_by_region(region_id)
        region.districts = districts
        return region
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to get region: {e}"
        )


@router.post(
    "/regions",
    tags=["Locations - Regions"],
    response_model=RegionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_region(
    payload: RegionCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new region."""
    try:
        return await LocationService(db).create_region(payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create region: {e}"
        )


@router.patch(
    "/regions/{region_id}",
    tags=["Locations - Regions"],
    response_model=RegionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_region(
    region_id: uuid.UUID,
    payload: RegionUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing region."""
    try:
        return await LocationService(db).update_region(region_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to update region: {e}"
        )


@router.delete(
    "/regions/{region_id}",
    tags=["Locations - Regions"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_region(
    region_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a region."""
    try:
        await LocationService(db).delete_region(region_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to delete region: {e}"
        )


#
# ─── DISTRICT ENDPOINTS ───────────────────────────────────────────────────────
#


@router.get(
    "/districts",
    tags=["Locations - Districts"],
    response_model=List[DistrictResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_districts(db: AsyncSession = Depends(get_async_db)):
    """List all districts."""
    try:
        return await LocationService(db).list_districts()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to list districts: {e}"
        )


@router.get(
    "/regions/{region_id}/districts",
    tags=["Locations - Districts"],
    response_model=List[DistrictResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_districts_by_region(
    region_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """List all districts in a given region."""
    try:
        return await LocationService(db).list_districts_by_region(region_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list districts by region: {e}",
        )


@router.get(
    "/districts/{district_id}",
    tags=["Locations - Districts"],
    response_model=DistrictResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_district(
    district_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a single district."""
    try:
        return await LocationService(db).get_district(district_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to get district: {e}"
        )


@router.post(
    "/districts",
    tags=["Locations - Districts"],
    response_model=DistrictResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_district(
    payload: DistrictCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new district."""
    try:
        return await LocationService(db).create_district(payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create district: {e}"
        )


@router.patch(
    "/districts/{district_id}",
    tags=["Locations - Districts"],
    response_model=DistrictResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_district(
    district_id: uuid.UUID,
    payload: DistrictUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing district."""
    try:
        return await LocationService(db).update_district(district_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to update district: {e}"
        )


@router.delete(
    "/districts/{district_id}",
    tags=["Locations - Districts"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_district(
    district_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a district."""
    try:
        await LocationService(db).delete_district(district_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to delete district: {e}"
        )
