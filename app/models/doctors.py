import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Float

from .base import SQLModel


class DoctorModel(SQLModel):
    __tablename__ = "doctors"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    professional = Column(String, nullable=True)
    about = Column(Text, nullable=True)
    photo = Column(Text, nullable=True)
    reyting = Column(Float, nullable=True)

    hospital_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital = relationship("HospitalModel", back_populates="doctors")

    # no delete‑orphan here, since FK is SET NULL
    queues = relationship("QueueModel", back_populates="doctor")
