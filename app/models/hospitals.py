import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON

from .base import SQLModel


class HospitalModel(SQLModel):
    __tablename__ = "hospitals"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    orientir = Column(String, nullable=True)
    photo = Column(Text, nullable=True)
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
    admin_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    coordinates = Column(String, nullable=True)
    admin = relationship("UserModel", back_populates="admin_hospital")
    working_hours = Column(JSON, nullable=True)

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
    services = relationship(
        "ServiceModel",
        back_populates="hospital",
        cascade="all, delete-orphan",
    )
