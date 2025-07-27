import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from .base import BaseSchema
from .hospitals import HospitalBasicSchema
from .doctors import DoctorBasicSchema
from .users import UserBasicSchema


class QueueCreateSchema(BaseModel):
    hospital_id: uuid.UUID
    user_id: uuid.UUID
    doctor_id: Optional[uuid.UUID] = None
    position: Optional[int] = None


class QueueUpdateSchema(BaseModel):
    hospital_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None
    position: Optional[int] = None
    status: Optional[str] = None
    called_at: Optional[datetime] = None
    served_at: Optional[datetime] = None


class QueueResponseSchema(BaseSchema):
    id: uuid.UUID
    hospital: HospitalBasicSchema
    user: UserBasicSchema
    doctor: Optional[DoctorBasicSchema]
    position: Optional[int]
    status: str
    called_at: Optional[datetime]
    served_at: Optional[datetime]
