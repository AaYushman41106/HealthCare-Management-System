from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.appointment import DoctorPublicResponse, PatientPublicResponse


class MedicalRecordCreateRequest(BaseModel):
    """Doctor request to create a medical record for a completed consultation.
    
    Doctor identity is derived from JWT. Patient identity is derived from the appointment.
    """
    appointment_id: int = Field(..., gt=0, description="Completed appointment reference ID")
    diagnosis: str = Field(..., min_length=3, max_length=500, description="Primary clinical diagnosis")
    symptoms: str = Field(..., min_length=3, max_length=500, description="Reported patient symptoms")
    treatment: str = Field(..., min_length=3, max_length=500, description="Administered or recommended treatment plan")
    prescription: Optional[str] = Field(default=None, max_length=2000, description="Prescribed medications, dosages, and instructions")
    notes: Optional[str] = Field(default=None, max_length=2000, description="Additional confidential physician notes")


class MedicalRecordResponse(BaseModel):
    """Sanitized medical record response excluding all authentication hashes and credentials."""
    id: int
    patient_id: int
    doctor_id: int
    appointment_id: int
    diagnosis: str
    symptoms: str
    treatment: str
    prescription: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    doctor: Optional[DoctorPublicResponse] = None
    patient: Optional[PatientPublicResponse] = None

    model_config = ConfigDict(from_attributes=True)
