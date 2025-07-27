import uuid
from typing import Optional
from pydantic import BaseModel
from .base import BaseSchema
from .hospitals import HospitalBasicSchema


class DoctorCreateSchema(BaseModel):
    first_name: str
    last_name: str
    professional: Optional[str] = None
    about: Optional[str] = None
    hospital_id: uuid.UUID


class DoctorUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    professional: Optional[str] = None
    about: Optional[str] = None
    hospital_id: Optional[uuid.UUID] = None


class DoctorResponseSchema(BaseSchema):
    id: uuid.UUID
    first_name: str
    last_name: str
    professional: Optional[str]
    about: Optional[str]
    hospital: HospitalBasicSchema


class DoctorBasicSchema(BaseSchema):
    id: uuid.UUID
    first_name: str
    last_name: str
