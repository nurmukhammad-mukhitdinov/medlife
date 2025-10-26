from sqlalchemy import Column, String, Boolean, Integer, Text, ForeignKey, Date, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid
from .base import SQLModel


class RoleModelLawyer(SQLModel):
    __tablename__ = "roles_lawyer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, unique=True, nullable=False)

    users = relationship("UserModelLawyer", back_populates="role")


class UserModelLawyer(SQLModel):
    __tablename__ = "users_lawyer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    email = Column(String, index=True, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles_lawyer.id"), nullable=True)
    role = relationship("RoleModelLawyer", back_populates="users")

    lawyers = relationship("LawyerModelLawyer", back_populates="user")
    # reviews = relationship("ReviewModelLawyer", back_populates="user")  # if you add reviews later


class RegionModelLawyer(SQLModel):
    __tablename__ = "regions_lawyer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, unique=True, nullable=False)

    districts = relationship("DistrictModelLawyer", back_populates="region")
    lawyers = relationship("LawyerModelLawyer", back_populates="region")


class DistrictModelLawyer(SQLModel):
    __tablename__ = "districts_lawyer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions_lawyer.id", ondelete="CASCADE"), nullable=False)

    region = relationship("RegionModelLawyer", back_populates="districts")
    lawyers = relationship("LawyerModelLawyer", back_populates="district")


class MiniCallCenterModelLawyer(SQLModel):
    __tablename__ = "mini_call_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    lawyers = relationship("LawyerModelLawyer", back_populates="mini_call_center")


class LawyerModelLawyer(SQLModel):
    __tablename__ = "lawyers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users_lawyer.id", ondelete="SET NULL"), nullable=True)
    user = relationship("UserModelLawyer", back_populates="lawyers")

    description = Column(Text, nullable=True)

    cases_participated = Column(Integer, default=0, nullable=False)
    cases_won = Column(Integer, default=0, nullable=False)

    license_number = Column(String, nullable=True)
    license_is_active = Column(Boolean, default=False, nullable=False)
    license_issued_at = Column(Date, nullable=True)
    license_expires_at = Column(Date, nullable=True)

    career_timeline = Column(JSONB, nullable=True)
    specializations = Column(ARRAY(String), nullable=True)
    experience_years = Column(Integer, nullable=True)
    photos = Column(JSONB, nullable=True)

    region_id = Column(UUID(as_uuid=True), ForeignKey("regions_lawyer.id", ondelete="SET NULL"), nullable=True)
    district_id = Column(UUID(as_uuid=True), ForeignKey("districts_lawyer.id", ondelete="SET NULL"), nullable=True)

    region = relationship("RegionModelLawyer", back_populates="lawyers")
    district = relationship("DistrictModelLawyer", back_populates="lawyers")

    organization_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_phone_reachable = Column(Boolean, default=True, nullable=False)

    mini_call_center_id = Column(UUID(as_uuid=True), ForeignKey("mini_call_centers.id", ondelete="SET NULL"), nullable=True)
    mini_call_center = relationship("MiniCallCenterModelLawyer", back_populates="lawyers")

    rating_average = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
