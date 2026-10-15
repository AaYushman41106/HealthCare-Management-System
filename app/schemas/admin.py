from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole


class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserStatusUpdateRequest(BaseModel):
    is_active: bool
    unlock: Optional[bool] = False


class DoctorAdminResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    user_email: Optional[str] = None
    user_username: Optional[str] = None
    user_is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorStatusUpdateRequest(BaseModel):
    is_active: bool


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    locked_accounts: int
    total_doctors: int
    active_doctors: int
    total_appointments: int
    total_medical_records: int
    total_audit_events: int
    recent_failed_logins: int
    security_alerts_count: int

    model_config = ConfigDict(from_attributes=True)
