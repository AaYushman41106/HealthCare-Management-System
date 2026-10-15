from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentUpdateRequest,
)
from app.services import appointment_service

router = APIRouter()


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new appointment (Patients only)",
)
def create_appointment(
    payload: AppointmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    """Book a new medical appointment.
    
    Security: The patient identity is strictly derived from the authenticated JWT token.
    Client-provided patient IDs are never trusted or accepted.
    """
    return appointment_service.create_appointment(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get(
    "",
    response_model=List[AppointmentResponse],
    summary="List appointments for current user (Role-aware)",
)
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AppointmentResponse]:
    """Retrieve appointments filtered by caller identity.
    
    PATIENTS see only their own appointments.
    DOCTORS see only appointments scheduled with them.
    Normal users never see an unrestricted global list of all appointments.
    """
    return appointment_service.get_appointments_for_user(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get single appointment details",
)
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    """Retrieve details for a single appointment if authorized."""
    return appointment_service.get_appointment_by_id(
        db=db,
        current_user=current_user,
        appointment_id=appointment_id,
    )


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update appointment status or doctor notes",
)
def patch_appointment(
    appointment_id: int,
    payload: AppointmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    """Update appointment status or clinical notes following strict role permissions and state transitions."""
    return appointment_service.update_appointment(
        db=db,
        current_user=current_user,
        appointment_id=appointment_id,
        payload=payload,
    )


@router.delete(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Safely cancel pending appointment (Patients only)",
)
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    """Safely cancel a patient's own pending appointment.
    
    Performs soft cancellation rather than destructive row deletion to maintain audit records.
    """
    return appointment_service.cancel_appointment_by_patient(
        db=db,
        current_user=current_user,
        appointment_id=appointment_id,
    )
