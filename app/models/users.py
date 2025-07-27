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
