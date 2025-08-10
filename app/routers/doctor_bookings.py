# app/routers/doctor_bookings.py
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models.users import UserModel
from app.service.doctor_bookings import DoctorBookingService
from app.schemas.doctor_bookings import (
    WorkingHoursSchema,
    AvailableSlotsResponse,
    BookingCreateSchema,
    BookingResponseSchema,
    BookingUpdateSchema,
    BookingListResponse,
)

router = APIRouter(tags=["Doctor Bookings"], prefix="/bookings")


# ---------- Bookings (CRUD over QueueModel) ----------

@router.get(
    "/all-bookings",
    response_model=List[BookingListResponse],
    summary="Get all bookings across all doctors",
)
async def get_all_bookings(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).get_all_bookings()


@router.get(
    "/{doctor_id:uuid}/bookings",
    response_model=List[BookingListResponse],
    summary="Get all bookings for a specific doctor",
)
async def get_bookings_for_doctor(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).get_bookings_for_doctor(doctor_id)


@router.post(
    "/{doctor_id:uuid}/book",
    response_model=BookingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Book a slot with a doctor",
)
async def book_slot(
    doctor_id: uuid.UUID,
    payload: BookingCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).book_slot(doctor_id, payload)


@router.patch(
    "/bookings/{booking_id:uuid}",
    response_model=BookingResponseSchema,
    summary="Edit an existing booking",
)
async def update_booking(
    booking_id: uuid.UUID,
    payload: BookingUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).update_booking(booking_id, payload)


@router.delete(
    "/bookings/{booking_id:uuid}",
    status_code=status.HTTP_200_OK,
    summary="Delete a booking",
)
async def delete_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).delete_booking(booking_id)


# ---------- Working hours & availability ----------

@router.get(
    "/{doctor_id:uuid}/working-hours",
    response_model=WorkingHoursSchema,
    summary="Get weekly working hours for a doctor",
)
async def get_working_hours(
    doctor_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).get_working_hours(doctor_id)


@router.get(
    "/{doctor_id:uuid}/available-slots",
    response_model=AvailableSlotsResponse,
    summary="Get free/booked half-hour slots for a date",
)
async def get_available_slots(
    doctor_id: uuid.UUID,
    date: str,  # format: YYYY-MM-DD
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await DoctorBookingService(db).get_available_slots(doctor_id, date)
