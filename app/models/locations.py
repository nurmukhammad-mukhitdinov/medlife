from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import SQLModel


class RegionModel(SQLModel):
    __tablename__ = "regions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name = Column(String, unique=True, nullable=False)

    districts = relationship(
        "DistrictModel",
        back_populates="region",
        cascade="all, delete-orphan",
    )
    hospitals = relationship(
        "HospitalModel",
        back_populates="region",
        cascade="all, delete-orphan",
    )


class DistrictModel(SQLModel):
    __tablename__ = "districts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name = Column(String, nullable=False)
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    )

    region = relationship("RegionModel", back_populates="districts")
    hospitals = relationship(
        "HospitalModel",
        back_populates="district",
        cascade="all, delete-orphan",
    )
