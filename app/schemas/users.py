import uuid
from datetime import datetime
from typing import Optional
from .base import BaseSchema
from pydantic import field_validator


class UseExistRequestSchema(BaseSchema):
    phone_number: str

    @field_validator("phone_number", mode="before")
    def validate_phone_number(cls, v):
        v = v.strip()
        if not v.startswith("+998") or len(v) != 13 or not v[4:].isdigit():
            raise ValueError("Phone number must be in format +998XXXXXXXXX")
        return v


class CheckUserExistsResponseSchema(BaseSchema):
    exists: bool


class RegisterRequestSchema(BaseSchema):
    phone_number: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str

    @field_validator("phone_number", mode="before")
    def validate_phone_number(cls, v):
        v = v.strip()
        if not v.startswith("+998") or len(v) != 13 or not v[4:].isdigit():
            raise ValueError("Phone number must be in format +998XXXXXXXXX")
        return v


class RegisterResponseSchema(BaseSchema):
    id: uuid.UUID
    phone_number: str
    email: Optional[str] = None
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime


class SignInRequestSchema(BaseSchema):
    phone_number: str
    password: str


class SignInResponseSchema(BaseSchema):
    access_token: str
    token_type: str
    expires_at: int


class UpdateUserRequestSchema(BaseSchema):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None


class UserBasicSchema(BaseSchema):
    id: uuid.UUID
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
