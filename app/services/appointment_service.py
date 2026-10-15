from datetime import date
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreateRequest, AppointmentUpdateRequest
from app.services.audit_service import log_event


def get_available_doctors(db: Session) -> List[Doctor]:
    """Retrieve all active doctors with sanitized public profile details."""
    return (
        db.query(Doctor)
        .join(Doctor.user)
        .filter(User.is_active.is_(True), Doctor.is_active.is_(True))
        .all()
    )


def create_appointment(
    db: Session,
    current_user: User,
    payload: AppointmentCreateRequest,
) -> Appointment:
    """Create a new appointment for the authenticated patient.
    
    Security: The patient_id is strictly derived from the authenticated user token.
    Collision Prevention: Prevents double-booking for the same doctor at the same date/time (PENDING/CONFIRMED).
    """
    if current_user.role != UserRole.PATIENT or not current_user.patient_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only patients are authorized to book appointments.",
        )

    # Validate target doctor exists and is active
    doctor = (
        db.query(Doctor)
        .join(Doctor.user)
        .filter(
            Doctor.id == payload.doctor_id,
            User.is_active.is_(True),
            Doctor.is_active.is_(True),
        )
        .first()
    )
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found or currently unavailable.",
        )

    # Appointment Collision Prevention:
    # A doctor cannot have two active (PENDING or CONFIRMED) appointments at the same date and time.
    active_collision = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == payload.appointment_date,
            Appointment.appointment_time == payload.appointment_time,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
        )
        .first()
    )
    if active_collision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Time slot ({payload.appointment_date} at {payload.appointment_time}) is already booked for Dr. {doctor.full_name or doctor.id}. Please choose another time.",
        )

    # Derive patient identity safely from token
    patient = current_user.patient_profile

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time,
        reason=payload.reason,
        status=AppointmentStatus.PENDING,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Audit logging
    log_event(
        db=db,
        action="APPOINTMENT_CREATED",
        resource_type="appointment",
        user_id=current_user.id,
        resource_id=appointment.id,
        details=f"Appointment #{appointment.id} created for {appointment.appointment_date} {appointment.appointment_time}",
    )

    return appointment


def get_appointments_for_user(db: Session, current_user: User) -> List[Appointment]:
    """Retrieve appointments filtered strictly by the user's role and identity.
    
    PATIENT: Only returns appointments belonging to this patient.
    DOCTOR: Only returns appointments assigned to this doctor.
    """
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile:
            return []
        return (
            db.query(Appointment)
            .filter(Appointment.patient_id == current_user.patient_profile.id)
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .all()
        )

    if current_user.role == UserRole.DOCTOR:
        if not current_user.doctor_profile:
            return []
        return (
            db.query(Appointment)
            .filter(Appointment.doctor_id == current_user.doctor_profile.id)
            .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
            .all()
        )

    return []


def get_appointment_by_id(db: Session, current_user: User, appointment_id: int) -> Appointment:
    """Retrieve an appointment by ID after verifying the authenticated user's authorization."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    # Check authorization based on role
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile or appointment.patient_id != current_user.patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot access another patient's appointment.",
            )

    elif current_user.role == UserRole.DOCTOR:
        if not current_user.doctor_profile or appointment.doctor_id != current_user.doctor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot access appointments assigned to another doctor.",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Unauthorized role.",
        )

    # Audit logging
    log_event(
        db=db,
        action="APPOINTMENT_VIEWED",
        resource_type="appointment",
        user_id=current_user.id,
        resource_id=appointment.id,
        details=f"Appointment #{appointment.id} viewed by {current_user.role.value}",
    )

    return appointment


def update_appointment(
    db: Session,
    current_user: User,
    appointment_id: int,
    payload: AppointmentUpdateRequest,
) -> Appointment:
    """Update appointment status or notes following role-based rules and state transitions."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    # PATIENT UPDATE RULES
    if current_user.role == UserRole.PATIENT:
        if not current_user.patient_profile or appointment.patient_id != current_user.patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot modify another patient's appointment.",
            )

        # Patients cannot update notes
        if payload.notes is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patients cannot add or modify doctor consultation notes.",
            )

        if payload.status is not None:
            # Patients can ONLY cancel their own appointment
            if payload.status in (
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.REJECTED,
                AppointmentStatus.COMPLETED,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access forbidden: Patients are not permitted to set status to {payload.status.value}.",
                )

            if payload.status == AppointmentStatus.CANCELLED:
                if appointment.status != AppointmentStatus.PENDING:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot cancel appointment with status {appointment.status.value}. Only PENDING appointments can be cancelled by patients.",
                    )
                appointment.status = AppointmentStatus.CANCELLED

    # DOCTOR UPDATE RULES
    elif current_user.role == UserRole.DOCTOR:
        if not current_user.doctor_profile or appointment.doctor_id != current_user.doctor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot modify appointments belonging to another doctor.",
            )

        if payload.status is not None:
            new_status = payload.status

            # Doctors cannot set to PENDING
            if new_status == AppointmentStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status transition: Doctors cannot revert an appointment to PENDING.",
                )

            # Terminal states check
            if appointment.status in (
                AppointmentStatus.COMPLETED,
                AppointmentStatus.REJECTED,
                AppointmentStatus.CANCELLED,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition: Appointment is in terminal status '{appointment.status.value}' and cannot be modified.",
                )

            # Valid transitions from PENDING: CONFIRMED, REJECTED, CANCELLED
            if appointment.status == AppointmentStatus.PENDING:
                if new_status == AppointmentStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid status transition: PENDING appointment must be CONFIRMED before being marked COMPLETED.",
                    )
                appointment.status = new_status

            # Valid transitions from CONFIRMED: COMPLETED, CANCELLED
            elif appointment.status == AppointmentStatus.CONFIRMED:
                if new_status not in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status transition: CONFIRMED appointment cannot transition to {new_status.value}.",
                    )
                appointment.status = new_status

        if payload.notes is not None:
            appointment.notes = payload.notes

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Unauthorized role.",
        )

    db.commit()
    db.refresh(appointment)

    # Audit logging
    log_action = "APPOINTMENT_CANCELLED" if payload.status == AppointmentStatus.CANCELLED else "APPOINTMENT_UPDATED"
    log_event(
        db=db,
        action=log_action,
        resource_type="appointment",
        user_id=current_user.id,
        resource_id=appointment.id,
        details=f"Appointment #{appointment.id} updated to status {appointment.status.value}",
    )

    return appointment


def cancel_appointment_by_patient(
    db: Session,
    current_user: User,
    appointment_id: int,
) -> Appointment:
    """Patient-initiated safe cancellation of a PENDING appointment (soft status update)."""
    if current_user.role != UserRole.PATIENT or not current_user.patient_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only patients can cancel appointments via this endpoint.",
        )

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if appointment.patient_id != current_user.patient_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot cancel another patient's appointment.",
        )

    if appointment.status != AppointmentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel appointment with status {appointment.status.value}. Only PENDING appointments can be cancelled.",
        )

    # Safe cancellation (preserve historical audit data instead of destructive delete)
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)

    # Audit logging
    log_event(
        db=db,
        action="APPOINTMENT_CANCELLED",
        resource_type="appointment",
        user_id=current_user.id,
        resource_id=appointment.id,
        details=f"Appointment #{appointment.id} cancelled by patient",
    )

    return appointment
