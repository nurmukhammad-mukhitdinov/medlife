import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from .base import BaseSchema
from pydantic import BaseModel, ConfigDict

class HospitalAdminBaseSchema(BaseSchema):
    phone_number: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class HospitalAdminCreateSchema(HospitalAdminBaseSchema):
    password: str
    hospital_id: uuid.UUID


class HospitalAdminUpdateSchema(BaseSchema):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class HospitalAdminResponseSchema(HospitalAdminBaseSchema):
    id: uuid.UUID
    hospital_id: Optional[uuid.UUID]
    model_config = ConfigDict(from_attributes=True)
