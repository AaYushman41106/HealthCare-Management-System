from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.database import get_db
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord
from app.models.user import User, UserRole
from app.schemas.admin import (
    AuditLogResponse,
    DoctorAdminResponse,
    DoctorStatusUpdateRequest,
    SecurityStatsResponse,
    UserAdminResponse,
    UserStatusUpdateRequest,
)
from app.services.audit_service import log_event

router = APIRouter()


@router.get(
    "/users",
    response_model=List[UserAdminResponse],
    summary="List all users with administrative details",
)
def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> List[User]:
    """Retrieve all users. Sensitive credentials like hashed_password are excluded."""
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.id.asc()).all()


@router.get(
    "/users/{user_id}",
    response_model=UserAdminResponse,
    summary="Get user details by ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> User:
    """Retrieve a single user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


@router.patch(
    "/users/{user_id}/status",
    response_model=UserAdminResponse,
    summary="Toggle user active status or unlock account",
)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> User:
    """Enable or disable user account or unlock locked accounts.
    
    Self-deactivation is prohibited to maintain administrative access.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Prevent administrative self-deactivation
    if user.id == current_admin.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account",
        )

    prev_status = user.is_active
    user.is_active = payload.is_active

    if payload.unlock or payload.is_active:
        user.failed_login_attempts = 0
        user.locked_until = None

    # If the user has a doctor profile, synchronize doctor active state
    if user.doctor_profile:
        user.doctor_profile.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    log_event(
        db=db,
        action="ADMIN_USER_STATUS_CHANGED",
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_admin.id,
        details=(
            f"Admin '{current_admin.username}' updated user '{user.username}' (ID: {user.id}) "
            f"status: is_active={prev_status}->{user.is_active}, unlocked={payload.unlock}"
        ),
    )

    return user


@router.get(
    "/doctors",
    response_model=List[DoctorAdminResponse],
    summary="List all doctors with user metadata",
)
def list_doctors(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> List[DoctorAdminResponse]:
    """Retrieve all doctor records along with associated user account info."""
    doctors = db.query(Doctor).join(Doctor.user).order_by(Doctor.id.asc()).all()
    results = []
    for doc in doctors:
        results.append(
            DoctorAdminResponse(
                id=doc.id,
                user_id=doc.user_id,
                full_name=doc.full_name,
                specialization=doc.specialization,
                license_number=doc.license_number,
                phone=doc.phone,
                is_active=doc.is_active,
                created_at=doc.created_at,
                user_email=doc.user.email if doc.user else None,
                user_username=doc.user.username if doc.user else None,
                user_is_active=doc.user.is_active if doc.user else None,
            )
        )
    return results


@router.get(
    "/doctors/{doctor_id}",
    response_model=DoctorAdminResponse,
    summary="Get doctor details by ID",
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> DoctorAdminResponse:
    """Retrieve doctor profile by ID."""
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found",
        )
    return DoctorAdminResponse(
        id=doc.id,
        user_id=doc.user_id,
        full_name=doc.full_name,
        specialization=doc.specialization,
        license_number=doc.license_number,
        phone=doc.phone,
        is_active=doc.is_active,
        created_at=doc.created_at,
        user_email=doc.user.email if doc.user else None,
        user_username=doc.user.username if doc.user else None,
        user_is_active=doc.user.is_active if doc.user else None,
    )


@router.patch(
    "/doctors/{doctor_id}/status",
    response_model=DoctorAdminResponse,
    summary="Toggle doctor active status",
)
def update_doctor_status(
    doctor_id: int,
    payload: DoctorStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> DoctorAdminResponse:
    """Update active status of doctor and synchronize underlying user account."""
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found",
        )

    prev_status = doc.is_active
    doc.is_active = payload.is_active
    if doc.user:
        doc.user.is_active = payload.is_active

    db.commit()
    db.refresh(doc)

    log_event(
        db=db,
        action="ADMIN_DOCTOR_STATUS_CHANGED",
        resource_type="doctor",
        resource_id=str(doc.id),
        user_id=current_admin.id,
        details=(
            f"Admin '{current_admin.username}' updated doctor '{doc.full_name}' (ID: {doc.id}) "
            f"active status: {prev_status}->{doc.is_active}"
        ),
    )

    return DoctorAdminResponse(
        id=doc.id,
        user_id=doc.user_id,
        full_name=doc.full_name,
        specialization=doc.specialization,
        license_number=doc.license_number,
        phone=doc.phone,
        is_active=doc.is_active,
        created_at=doc.created_at,
        user_email=doc.user.email if doc.user else None,
        user_username=doc.user.username if doc.user else None,
        user_is_active=doc.user.is_active if doc.user else None,
    )


@router.get(
    "/audit-logs",
    response_model=List[AuditLogResponse],
    summary="Query audit trail with administrative filters",
)
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> List[AuditLog]:
    """Retrieve audit events matching optional filters. Self-logs viewing action."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    # Self-log admin audit log viewing after fetching to avoid recursive log inflation
    log_event(
        db=db,
        action="ADMIN_AUDIT_LOG_VIEWED",
        resource_type="audit_logs",
        user_id=current_admin.id,
        details=(
            f"Admin '{current_admin.username}' inspected audit trail "
            f"(filters: action={action}, resource_type={resource_type}, user_id={user_id}, limit={limit})"
        ),
    )

    return logs


@router.get(
    "/security-stats",
    response_model=SecurityStatsResponse,
    summary="Get security statistics and system monitoring overview",
)
def get_security_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> SecurityStatsResponse:
    """Retrieve aggregated system health, security event counts, and lockout numbers."""
    now = datetime.now(timezone.utc)

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    inactive_users = db.query(User).filter(User.is_active.is_(False)).count()

    users_with_locks = db.query(User).filter(User.locked_until.isnot(None)).all()
    locked_accounts = sum(
        1
        for u in users_with_locks
        if u.locked_until
        and (
            u.locked_until.replace(tzinfo=timezone.utc)
            if u.locked_until.tzinfo is None
            else u.locked_until
        )
        > now
    )

    total_doctors = db.query(Doctor).count()
    active_doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).count()
    total_appointments = db.query(Appointment).count()
    total_medical_records = db.query(MedicalRecord).count()
    total_audit_events = db.query(AuditLog).count()
    recent_failed_logins = (
        db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILURE").count()
    )
    locked_events_count = (
        db.query(AuditLog).filter(AuditLog.action == "ACCOUNT_LOCKED").count()
    )

    security_alerts_count = locked_accounts + locked_events_count + recent_failed_logins

    # Self-log admin viewing security stats
    log_event(
        db=db,
        action="ADMIN_SECURITY_STATS_VIEWED",
        resource_type="security_stats",
        user_id=current_admin.id,
        details=f"Admin '{current_admin.username}' viewed security stats dashboard",
    )

    return SecurityStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        locked_accounts=locked_accounts,
        total_doctors=total_doctors,
        active_doctors=active_doctors,
        total_appointments=total_appointments,
        total_medical_records=total_medical_records,
        total_audit_events=total_audit_events,
        recent_failed_logins=recent_failed_logins,
        security_alerts_count=security_alerts_count,
    )
