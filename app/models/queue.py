import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import SQLModel


class QueueModel(SQLModel):
    __tablename__ = "queues"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id = Column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    appointment_date = Column(DateTime, nullable=False)  # e.g., 2025-08-12
    appointment_start = Column(DateTime, nullable=False)  # e.g., 09:30
    appointment_end = Column(DateTime, nullable=False)  # e.g., 10:00
    position = Column(Integer, nullable=True)
    status = Column(String, default="waiting", nullable=False)
    called_at = Column(DateTime, nullable=True)
    served_at = Column(DateTime, nullable=True)

    hospital = relationship("HospitalModel", back_populates="queues")
    doctor = relationship("DoctorModel", back_populates="queues")
    user = relationship("UserModel", back_populates="queues")
