from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
import uuid
from datetime import date
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


class CreateUserDetailRequest(BaseSchema):
    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    blood_sugar_mg_dl: Optional[float] = None
    bp_systolic_mm_hg: Optional[int] = None
    bp_diastolic_mm_hg: Optional[int] = None
    cholesterol_mg_dl: Optional[float] = None
    hemoglobin_g_dl: Optional[float] = None


class UpdateUserDetailRequest(BaseSchema):
    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    blood_sugar_mg_dl: Optional[float] = None
    bp_systolic_mm_hg: Optional[int] = None
    bp_diastolic_mm_hg: Optional[int] = None
    cholesterol_mg_dl: Optional[float] = None
    hemoglobin_g_dl: Optional[float] = None


class UserDetailResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID

    region_id: Optional[uuid.UUID]
    region_name: Optional[str]

    district_id: Optional[uuid.UUID]
    district_name: Optional[str]

    height_cm: Optional[int]
    weight_kg: Optional[int]
    blood_sugar_mg_dl: Optional[float]
    bp_systolic_mm_hg: Optional[int]
    bp_diastolic_mm_hg: Optional[int]
    cholesterol_mg_dl: Optional[float]
    hemoglobin_g_dl: Optional[float]


# ===== LAWYERS =====
class LawyerCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    cases_participated: Optional[int] = 0
    cases_won: Optional[int] = 0

    license_number: Optional[str] = None
    license_is_active: Optional[bool] = False
    license_issued_at: Optional[date] = None
    license_expires_at: Optional[date] = None

    career_timeline: Optional[List[Dict[str, Any]]] = None
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = None
    photos: Optional[List[Dict[str, Any]]] = None

    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None

    organization_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_phone_reachable: Optional[bool] = True
    mini_call_center_id: Optional[uuid.UUID] = None

    is_active: Optional[bool] = True


class LawyerUpdate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    cases_participated: Optional[int] = None
    cases_won: Optional[int] = None

    license_number: Optional[str] = None
    license_is_active: Optional[bool] = None
    license_issued_at: Optional[date] = None
    license_expires_at: Optional[date] = None

    career_timeline: Optional[List[Dict[str, Any]]] = None
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = None
    photos: Optional[List[Dict[str, Any]]] = None

    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None

    organization_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_phone_reachable: Optional[bool] = None
    mini_call_center_id: Optional[uuid.UUID] = None

    is_active: Optional[bool] = None


class LawyerOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    cases_participated: int
    cases_won: int

    license_number: Optional[str] = None
    license_is_active: bool
    license_issued_at: Optional[date] = None
    license_expires_at: Optional[date] = None

    career_timeline: Optional[List[Dict[str, Any]]] = None
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = None
    photos: Optional[List[Dict[str, Any]]] = None

    region_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None

    organization_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_phone_reachable: bool
    mini_call_center_id: Optional[uuid.UUID] = None

    is_active: bool

    class Config:
        from_attributes = True
