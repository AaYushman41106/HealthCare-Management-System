from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.appointment import DoctorPublicResponse
from app.services import appointment_service

router = APIRouter()


@router.get(
    "",
    response_model=List[DoctorPublicResponse],
    summary="List available active doctors",
)
def list_doctors(db: Session = Depends(get_db)) -> List[DoctorPublicResponse]:
    """Return a sanitized list of available doctors for patient scheduling.
    
    Excludes passwords, internal hashes, and sensitive authentication fields.
    """
    doctors = appointment_service.get_available_doctors(db)
    return doctors
