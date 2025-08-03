import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey

from .base import SQLModel


class RoleModel(SQLModel):
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    name = Column(String, unique=True, nullable=False)

    users = relationship("UserModel", back_populates="role")


class UserModel(SQLModel):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    phone_number = Column(String, unique=True, nullable=False)
    email = Column(String, index=True, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    role = relationship("RoleModel", back_populates="users")

    queues = relationship(
        "QueueModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    details = relationship(
        "UserDetailModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chats = relationship(
        "ChatHistoryModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class UserDetailModel(SQLModel):
    __tablename__ = "user_details"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    # link back to UserModel (one-to-one)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # optional region & district
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
    )
    district_id = Column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # basic anthropometrics
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)

    # simple lab results
    blood_sugar_mg_dl = Column(Float, nullable=True)
    bp_systolic_mm_hg = Column(Integer, nullable=True)
    bp_diastolic_mm_hg = Column(Integer, nullable=True)
    cholesterol_mg_dl = Column(Float, nullable=True)
    hemoglobin_g_dl = Column(Float, nullable=True)

    # relationships
    user = relationship("UserModel", back_populates="details")
    region = relationship(
        "RegionModel",
        back_populates="user_details",
    )
    district = relationship(
        "DistrictModel",
        back_populates="user_details",
    )
