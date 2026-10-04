from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Alphanumeric username (3-50 chars)")
    email: EmailStr = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password with min 8 characters")
    role: Optional[str] = Field(default=None, description="Role selection (only PATIENT allowed publicly)")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Optional full name of the patient")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean_user = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", clean_user):
            raise ValueError("Username may only contain letters, numbers, underscores, and hyphens.")
        return clean_user

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean_role = v.strip().upper()
            if clean_role != UserRole.PATIENT.value:
                raise ValueError("Public registration as ADMIN or DOCTOR is not permitted. Only PATIENT role is allowed.")
            return clean_role
        return v


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Plaintext account password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
