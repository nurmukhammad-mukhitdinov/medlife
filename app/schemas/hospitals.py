import uuid
from typing import Optional
from pydantic import BaseModel
from .base import BaseSchema
from .locations import (
    RegionBasicSchema,
    DistrictBasicSchema,
)
from pydantic import BaseModel, Field


class HospitalCreateSchema(BaseModel):
    name: str
    address: Optional[str] = None
    orientir: Optional[str] = None
    region_id: uuid.UUID
    district_id: uuid.UUID


class HospitalUpdateSchema(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    orientir: Optional[str] = None
    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None


#
# ─── HOSPITAL RESPONSE SCHEMA ───────────────────────────────────────────────────────
class HospitalBasicSchema(BaseSchema):
    id: uuid.UUID
    name: str


class HospitalResponseSchema(BaseSchema):
    id: uuid.UUID
    name: str
    address: Optional[str]
    orientir: Optional[str]
    reyting:Optional[float]
    region: RegionBasicSchema
    district: DistrictBasicSchema
