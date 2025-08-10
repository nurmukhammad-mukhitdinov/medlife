import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import SQLModel


class ServiceModel(SQLModel):
    __tablename__ = "services"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    name = Column(String, nullable=False)  # e.g., "Consultation"
    description = Column(Text, nullable=True)  # optional details
    price = Column(Float, nullable=False)  # service cost

    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=True,
    )
    doctor_id = Column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=True
    )

    hospital = relationship("HospitalModel", back_populates="services")
    doctor = relationship("DoctorModel", back_populates="services")
