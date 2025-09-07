# app/models/medicine_reminders.py
import uuid
from datetime import datetime, time
from sqlalchemy import Column, String, Time, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import SQLModel

class MedicineReminderModel(SQLModel):
    __tablename__ = "medicine_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    medicine_name = Column(String, nullable=False)
    remind_time = Column(Time, nullable=False)  # daily reminder time
    repeat_daily = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="medicine_reminders")
