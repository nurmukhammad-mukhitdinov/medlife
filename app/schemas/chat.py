# app/schemas/chat.py

import uuid
from uuid import UUID
from datetime import datetime
from typing import List

from .base import BaseSchema


class MessageSchema(BaseSchema):
    content: str


class ChatRequestSchema(BaseSchema):
    messages: List[MessageSchema]


class ChatResponseSchema(BaseSchema):
    reply: str
    conversation_id: UUID


class ChatHistoryResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID
    prompt: str
    response: str
    created_at: datetime




class ChatThreadMessage(BaseSchema):
    prompt: str
    response: str
    created_at: datetime




class ConversationDetailResponse(BaseSchema):
    conversation_id: UUID
    messages: List[ChatThreadMessage]




class ConversationSummaryResponse(BaseSchema):
    conversation_id: UUID
    prompt: str
    response: str
    created_at: datetime


