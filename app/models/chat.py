# app/models/chat_history.py
import uuid
from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import SQLModel
from sqlalchemy.orm import relationship


class ChatHistoryModel(SQLModel):
    __tablename__ = "chat_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id = Column(  # must be non-null
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        index=True,
        nullable=False,
    )
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    user = relationship("UserModel", back_populates="chats")
