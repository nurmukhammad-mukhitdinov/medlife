import uuid
from datetime import datetime
from sqlalchemy import Column, Text, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import SQLModel


class ClinicChatModel(SQLModel):

    __tablename__ = "clinic_chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


    hospital = relationship("HospitalModel", back_populates="clinic_chats")
    user = relationship("UserModel", back_populates="clinic_chats")
    messages = relationship(
        "ClinicChatMessageModel",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ClinicChatMessageModel.created_at.asc()",
    )


class ClinicChatMessageModel(SQLModel):
    """
    Messages inside a clinic chat.
    """
    __tablename__ = "clinic_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("clinic_chats.id", ondelete="CASCADE"), nullable=False)

    sender_type = Column(String, nullable=False)  # "USER" or "HOSPITAL"
    text = Column(Text, nullable=False)

    thread = relationship("ClinicChatModel", back_populates="messages")
