# app/schemas/__init__.py
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.appointment import (
    DoctorPublicResponse,
    PatientPublicResponse,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentResponse,
)
from app.schemas.medical_record import (
    MedicalRecordCreateRequest,
    MedicalRecordResponse,
)
from app.schemas.admin import (
    UserAdminResponse,
    UserStatusUpdateRequest,
    DoctorAdminResponse,
    DoctorStatusUpdateRequest,
    AuditLogResponse,
    SecurityStatsResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserResponse",
    "DoctorPublicResponse",
    "PatientPublicResponse",
    "AppointmentCreateRequest",
    "AppointmentUpdateRequest",
    "AppointmentResponse",
    "MedicalRecordCreateRequest",
    "MedicalRecordResponse",
    "UserAdminResponse",
    "UserStatusUpdateRequest",
    "DoctorAdminResponse",
    "DoctorStatusUpdateRequest",
    "AuditLogResponse",
    "SecurityStatsResponse",
]
