import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import SQLModel


class HospitalModel(SQLModel):
    __tablename__ = "hospitals"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    orientir = Column(String, nullable=True)
    photo       = Column(Text, nullable=True)
    reyting = Column(Float, nullable=True)

    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    district_id = Column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="RESTRICT"),
        nullable=False,
    )

    region = relationship("RegionModel", back_populates="hospitals")
    district = relationship("DistrictModel", back_populates="hospitals")
    doctors = relationship(
        "DoctorModel",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )
    queues = relationship(
        "QueueModel",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )
