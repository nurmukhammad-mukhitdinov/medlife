import uuid
from typing import Optional
from pydantic import BaseModel
from .base import BaseSchema
from .hospitals import HospitalBasicSchema
from pydantic import BaseModel, Field
from .doctor_bookings import WorkingHoursSchema

class DoctorCreateSchema(BaseModel):
    first_name: str
    last_name: str
    professional: Optional[str] = None
    about: Optional[str] = None
    hospital_id: uuid.UUID
    working_hours: Optional[WorkingHoursSchema] = None


class DoctorUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    professional: Optional[str] = None
    about: Optional[str] = None
    hospital_id: Optional[uuid.UUID] = None
    working_hours: Optional[WorkingHoursSchema] = None


class DoctorResponseSchema(BaseSchema):
    id: uuid.UUID
    first_name: str
    last_name: str
    professional: Optional[str]
    about: Optional[str]
    reyting: Optional[float]
    hospital: HospitalBasicSchema
    working_hours: Optional[WorkingHoursSchema] = None


class DoctorBasicSchema(BaseSchema):
    id: uuid.UUID
    first_name: str
    last_name: str
