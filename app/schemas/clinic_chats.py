import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field
from .base import BaseSchema


class ClinicChatMessageCreate(BaseSchema):
    text: str = Field(..., min_length=1, max_length=4000)


class ClinicChatMessageResponse(BaseSchema):
    id: uuid.UUID
    sender_type: str
    text: str
    created_at: datetime


class ClinicChatLite(BaseSchema):
    id: uuid.UUID
    hospital_id: uuid.UUID
    user_id: uuid.UUID
    last_message: Optional[ClinicChatMessageResponse] = None


class ClinicChatResponse(BaseSchema):
    id: uuid.UUID
    hospital_id: uuid.UUID
    user_id: uuid.UUID
    # IMPORTANT: avoid mutable default
    messages: List[ClinicChatMessageResponse] = Field(default_factory=list)
