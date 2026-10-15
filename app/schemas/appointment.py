from datetime import date, datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.appointment import AppointmentStatus


class DoctorPublicResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatientPublicResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreateRequest(BaseModel):
    """Appointment booking payload. Note: patient_id is NOT accepted from client."""
    doctor_id: int = Field(..., gt=0, description="Target Doctor ID")
    appointment_date: date = Field(..., description="Desired appointment date (YYYY-MM-DD)")
    appointment_time: str = Field(..., description="Time of appointment in HH:MM format")
    reason: str = Field(..., min_length=3, max_length=500, description="Brief reason for consultation")

    @field_validator("appointment_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        clean_time = v.strip()
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", clean_time):
            raise ValueError("Time must be in 24-hour HH:MM format (e.g., 09:30, 14:00).")
        # Standardize to 5 characters, e.g. '9:30' -> '09:30'
        parts = clean_time.split(":")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"

    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Appointment date cannot be in the past.")
        return v


class AppointmentUpdateRequest(BaseModel):
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = Field(default=None, max_length=1000, description="Doctor consultation notes")


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: str
    reason: str
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    doctor: Optional[DoctorPublicResponse] = None
    patient: Optional[PatientPublicResponse] = None

    model_config = ConfigDict(from_attributes=True)
