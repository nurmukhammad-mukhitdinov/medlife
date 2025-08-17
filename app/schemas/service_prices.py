import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from .base import BaseSchema


class ServicePriceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    hospital_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None


class ServicePriceCreate(ServicePriceBase):
    pass


class ServicePriceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    hospital_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None


class ServicePriceResponse(BaseSchema):
    id: uuid.UUID
    name: str
    description: Optional[str]
    price: float
    hospital_id: Optional[uuid.UUID]
    doctor_id: Optional[uuid.UUID]


class ServicePriceListResponse(BaseSchema):
    items: List[ServicePriceResponse]
    total: int
