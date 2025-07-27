import uuid
from typing import List
from .base import BaseSchema
from typing import Optional


class RegionBasicSchema(BaseSchema):
    id: uuid.UUID
    name: str


class DistrictBasicSchema(BaseSchema):
    id: uuid.UUID
    name: str


class RegionResponseSchema(BaseSchema):
    id: uuid.UUID
    name: str


class RegionWithDistrictsSchema(BaseSchema):
    districts: List[DistrictBasicSchema]


class DistrictResponseSchema(BaseSchema):
    id: uuid.UUID
    name: str
    region: RegionBasicSchema


class RegionCreateSchema(BaseSchema):
    name: str


class RegionUpdateSchema(BaseSchema):
    name: Optional[str] = None


class DistrictCreateSchema(BaseSchema):
    name: str
    region_id: uuid.UUID


class DistrictUpdateSchema(BaseSchema):
    name: Optional[str] = None
    region_id: Optional[uuid.UUID] = None
