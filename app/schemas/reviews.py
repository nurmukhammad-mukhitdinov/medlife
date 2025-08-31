import uuid
from typing import Optional, List
from .base import BaseSchema
from pydantic import Field


class ReviewCreateSchema(BaseSchema):
    hospital_id: uuid.UUID
    comment: str = Field(..., min_length=1, max_length=2000)


class ReviewUpdateSchema(BaseSchema):
    comment: Optional[str] = Field(None, min_length=1, max_length=2000)


class ReviewResponseSchema(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    hospital_id: uuid.UUID
    comment: str


class ReviewListResponse(BaseSchema):
    items: List[ReviewResponseSchema]
    total: int
