from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordCreateRequest,
    MedicalRecordResponse,
)
from app.services import medical_record_service

router = APIRouter()


@router.post(
    "",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create medical record for completed consultation (Doctors only)",
)
def create_record(
    payload: MedicalRecordCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalRecordResponse:
    """Create a new medical record for an eligible completed appointment.
    
    Doctor identity is derived from JWT. Patient identity is derived from the appointment.
    """
    return medical_record_service.create_medical_record(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get(
    "",
    response_model=List[MedicalRecordResponse],
    summary="List accessible medical records (Role-filtered)",
)
def list_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MedicalRecordResponse]:
    """Retrieve medical records.
    
    PATIENTS view only their own medical records.
    DOCTORS view only medical records from consultations they conducted.
    """
    return medical_record_service.get_medical_records(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{record_id}",
    response_model=MedicalRecordResponse,
    summary="Get single medical record details",
)
def get_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalRecordResponse:
    """Retrieve a specific medical record after ownership verification."""
    return medical_record_service.get_medical_record_by_id(
        db=db,
        current_user=current_user,
        record_id=record_id,
    )
