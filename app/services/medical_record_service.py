from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import MedicalRecord
from app.models.user import User, UserRole
from app.schemas.medical_record import MedicalRecordCreateRequest
from app.services.audit_service import log_event


def create_medical_record(
    db: Session,
    current_user: User,
    payload: MedicalRecordCreateRequest,
) -> MedicalRecord:
    """Create a medical record for a completed consultation.
    
    Security: Doctor identity is derived from JWT. Patient identity is derived from the appointment.
    Pre-condition: Appointment must be COMPLETED and belong to this doctor.
    """
    if current_user.role != UserRole.DOCTOR or not current_user.doctor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only doctors are authorized to create medical records.",
        )

    appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    # Verify doctor authorization
    if appointment.doctor_id != current_user.doctor_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot create medical records for another doctor's consultation.",
        )

    # Verify consultation is completed
    if appointment.status != AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Medical records can only be created for COMPLETED appointments. Current appointment status is '{appointment.status.value}'.",
        )

    # Check for duplicate record
    existing = db.query(MedicalRecord).filter(MedicalRecord.appointment_id == appointment.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A medical record already exists for this appointment.",
        )

    # Derive patient identity safely from appointment
    record = MedicalRecord(
        patient_id=appointment.patient_id,
        doctor_id=current_user.doctor_profile.id,
        appointment_id=appointment.id,
        diagnosis=payload.diagnosis,
        symptoms=payload.symptoms,
        treatment=payload.treatment,
        prescription=payload.prescription,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Audit logging
    log_event(
        db=db,
        action="MEDICAL_RECORD_CREATED",
        resource_type="medical_record",
        user_id=current_user.id,
        resource_id=record.id,
        details=f"Medical record #{record.id} created for appointment #{appointment.id}",
    )

    return record


def get_medical_records(db: Session, current_user: User) -> List[MedicalRecord]:
    """Retrieve medical records filtered strictly by caller identity and role.
    
    PATIENTS view only their own medical records.
    DOCTORS view only medical records from consultations they conducted.
    """
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile:
            return []
        return (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == current_user.patient_profile.id)
            .order_by(MedicalRecord.created_at.desc())
            .all()
        )

    if current_user.role == UserRole.DOCTOR:
        if not current_user.doctor_profile:
            return []
        return (
            db.query(MedicalRecord)
            .filter(MedicalRecord.doctor_id == current_user.doctor_profile.id)
            .order_by(MedicalRecord.created_at.desc())
            .all()
        )

    return []


def get_medical_record_by_id(
    db: Session,
    current_user: User,
    record_id: int,
) -> MedicalRecord:
    """Retrieve a single medical record if caller is authorized.
    
    Logs an audit event for both successful viewing and denied access attempts.
    """
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found.",
        )

    # Ownership checks
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile or record.patient_id != current_user.patient_profile.id:
            log_event(
                db=db,
                action="MEDICAL_RECORD_ACCESS_DENIED",
                resource_type="medical_record",
                user_id=current_user.id,
                resource_id=record_id,
                details="Patient attempted unauthorized access to another patient's medical record",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot access another patient's medical record.",
            )

    elif current_user.role == UserRole.DOCTOR:
        if not current_user.doctor_profile or record.doctor_id != current_user.doctor_profile.id:
            log_event(
                db=db,
                action="MEDICAL_RECORD_ACCESS_DENIED",
                resource_type="medical_record",
                user_id=current_user.id,
                resource_id=record_id,
                details="Doctor attempted unauthorized access to another doctor's medical record",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot access medical records created by another doctor.",
            )

    else:
        log_event(
            db=db,
            action="MEDICAL_RECORD_ACCESS_DENIED",
            resource_type="medical_record",
            user_id=current_user.id,
            resource_id=record_id,
            details="Unauthorized role attempted medical record access",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Unauthorized role.",
        )

    # Successful view audit event
    log_event(
        db=db,
        action="MEDICAL_RECORD_VIEWED",
        resource_type="medical_record",
        user_id=current_user.id,
        resource_id=record.id,
        details=f"Medical record #{record.id} viewed by {current_user.role.value}",
    )

    return record
