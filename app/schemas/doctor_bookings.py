import uuid
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel
from .base import BaseSchema


class WorkingHoursSchema(BaseSchema):
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None


class SlotSchema(BaseSchema):
    start: str  # "09:00"
    end: str  # "09:30"
    status: str  # "free" or "booked"


class AvailableSlotsResponse(BaseSchema):
    date: date
    slots: List[SlotSchema]


class BookingCreateSchema(BaseSchema):
    user_id: uuid.UUID
    date: date
    start_time: str  # "09:00"
    end_time: str  # "09:30"


class BookingResponseSchema(BaseSchema):
    id: uuid.UUID
    doctor_id: Optional[uuid.UUID]
    hospital_id: uuid.UUID
    user_id: uuid.UUID
    appointment_date: datetime
    appointment_start: datetime
    appointment_end: datetime
    status: str


class BookingUpdateSchema(BaseSchema):
    date: Optional[date] = None
    start_time: Optional[str] = None  # "HH:MM"
    end_time: Optional[str] = None  # "HH:MM"
    status: Optional[str] = None


class BookingListResponse(BaseSchema):
    id: uuid.UUID
    doctor_id: Optional[uuid.UUID]
    hospital_id: uuid.UUID
    user_id: uuid.UUID
    appointment_date: datetime
    appointment_start: datetime
    appointment_end: datetime
    status: str
