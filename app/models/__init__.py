# app/models/__init__.py
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import MedicalRecord
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "UserRole",
    "Patient",
    "Doctor",
    "Appointment",
    "AppointmentStatus",
    "MedicalRecord",
    "AuditLog",
]
